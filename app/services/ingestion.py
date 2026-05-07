# Servicio de ingesta de datos F1.
#
# Concepto clave — Capa de servicios:
#   Los endpoints (app/api/) solo reciben requests y devuelven responses.
#   La lógica de negocio (descargar datos, transformar, guardar) vive acá.
#   Esto permite testear la lógica sin levantar un servidor HTTP.
#
# Flujo de ingesta:
#   1. fastf1 descarga los datos de la sesión (con caché local en data/)
#   2. Transformamos los DataFrames de pandas en modelos SQLAlchemy
#   3. Guardamos en PostgreSQL
#   4. Es idempotente: si la sesión ya existe, se reemplazan sus vueltas

from __future__ import annotations

import logging

import fastf1
import pandas as pd
from sqlalchemy.orm import Session

from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funciones auxiliares (puras — no tocan la DB, fáciles de testear)
# ---------------------------------------------------------------------------


def timedelta_to_ms(td: object) -> float | None:
    """
    Convierte un pandas Timedelta a milisegundos.
    Devuelve None para NaT, None o cualquier valor no-numérico.

    Ejemplo:
        timedelta_to_ms(pd.Timedelta(seconds=80.5))  → 80500.0
        timedelta_to_ms(pd.NaT)                       → None
    """
    try:
        if pd.isna(td):
            return None
    except (TypeError, ValueError):
        return None
    return td.total_seconds() * 1000


def is_valid_lap(lap_row: pd.Series) -> bool:
    """
    Determina si una vuelta tiene datos suficientes para guardar.
    Filtramos vueltas sin tiempo (típicamente in-laps y out-laps).
    """
    lap_time = lap_row.get("LapTime")
    lap_number = lap_row.get("LapNumber")
    try:
        return not pd.isna(lap_time) and not pd.isna(lap_number)
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Funciones de DB
# ---------------------------------------------------------------------------


def get_or_create_driver(
    db: Session,
    code: str,
    full_name: str,
    team: str | None,
) -> Driver:
    """
    Busca un piloto por código. Si no existe, lo crea.
    Si existe, actualiza su equipo (puede cambiar entre temporadas).

    db.flush() escribe en la transacción actual sin hacer COMMIT.
    Así el driver.id está disponible antes de insertar las vueltas.
    """
    driver = db.query(Driver).filter(Driver.code == code).first()
    if driver is None:
        driver = Driver(code=code, full_name=full_name, team=team)
        db.add(driver)
        db.flush()
        logger.info("Nuevo piloto creado: %s (%s)", code, full_name)
    else:
        driver.team = team
    return driver


def upsert_f1_session(
    db: Session,
    year: int,
    grand_prix: str,
    session_type: str,
    session_date: object,
) -> tuple[F1Session, bool]:
    """
    Busca una sesión en la DB. Si no existe, la crea.
    Devuelve (sesión, is_new).

    Si ya existe, borra todas sus vueltas previas para re-ingesta limpia.
    Esto garantiza idempotencia: correr el script dos veces da el mismo resultado.
    """
    db_session = (
        db.query(F1Session)
        .filter(
            F1Session.year == year,
            F1Session.grand_prix == grand_prix,
            F1Session.session_type == session_type,
        )
        .first()
    )

    if db_session is None:
        db_session = F1Session(
            year=year,
            grand_prix=grand_prix,
            session_type=session_type,
            session_date=session_date,
        )
        db.add(db_session)
        db.flush()
        return db_session, True
    else:
        # Borra las vueltas previas para reemplazarlas con los datos frescos
        deleted = db.query(Lap).filter(Lap.session_id == db_session.id).delete()
        logger.info("Sesión existente — %d vueltas previas eliminadas", deleted)
        return db_session, False


def build_lap(
    session_id: int,
    driver_id: int,
    lap_row: pd.Series,
) -> Lap:
    """Construye un objeto Lap a partir de una fila del DataFrame de fastf1."""
    is_pb_raw = lap_row.get("IsPersonalBest", False)
    try:
        is_personal_best = bool(is_pb_raw) if not pd.isna(is_pb_raw) else False
    except (TypeError, ValueError):
        is_personal_best = False

    return Lap(
        session_id=session_id,
        driver_id=driver_id,
        lap_number=int(lap_row["LapNumber"]),
        lap_time_ms=timedelta_to_ms(lap_row.get("LapTime")),
        sector1_ms=timedelta_to_ms(lap_row.get("Sector1Time")),
        sector2_ms=timedelta_to_ms(lap_row.get("Sector2Time")),
        sector3_ms=timedelta_to_ms(lap_row.get("Sector3Time")),
        is_personal_best=is_personal_best,
    )


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------


def ingest_session(
    db: Session,
    year: int,
    grand_prix: str,
    session_type: str,
    cache_path: str = "data/",
) -> dict:
    """
    Descarga una sesión de F1 con fastf1 y la guarda en la base de datos.

    Args:
        db:           Sesión de SQLAlchemy (viene de get_db o del script CLI).
        year:         Año de la temporada (ej: 2024).
        grand_prix:   Nombre del GP (ej: "Miami", "Monza").
        session_type: Tipo de sesión: Q, R, FP1, FP2, FP3, S, SQ.
        cache_path:   Carpeta donde fastf1 guarda los datos descargados.

    Returns:
        dict con session_id, drivers_count, laps_count.
    """
    logger.info("Iniciando ingesta: %d %s %s", year, grand_prix, session_type)

    # 1. Activar caché y cargar sesión
    #    telemetry=False → no descarga datos por muestra (más liviano)
    #    laps=True      → sí descarga datos de vueltas
    fastf1.Cache.enable_cache(cache_path)
    ff1_session = fastf1.get_session(year, grand_prix, session_type)
    ff1_session.load(telemetry=False, laps=True, weather=False, messages=False)

    # 2. Extraer fecha de la sesión con manejo de None/NaT
    session_date = None
    try:
        if ff1_session.date and not pd.isna(ff1_session.date):
            session_date = ff1_session.date.date()
    except (AttributeError, TypeError, ValueError):
        pass

    # 3. Crear o actualizar la sesión en DB
    db_session, is_new = upsert_f1_session(
        db, year, grand_prix, session_type, session_date
    )
    action = "creada" if is_new else "actualizada"
    logger.info("Sesión %s (id=%d)", action, db_session.id)

    # 4. Procesar pilotos únicos que aparecen en las vueltas
    laps_df = ff1_session.laps
    drivers_map: dict[str, Driver] = {}

    for driver_code in laps_df["Driver"].dropna().unique():
        try:
            info = ff1_session.get_driver(driver_code)
            full_name = info.get("FullName") or info.get("BroadcastName") or driver_code
            team = info.get("TeamName") or None
        except Exception:
            full_name = driver_code
            team = None

        drivers_map[driver_code] = get_or_create_driver(
            db, driver_code, full_name, team
        )

    # 5. Construir e insertar vueltas válidas
    laps_to_insert = []
    for _, lap_row in laps_df.iterrows():
        driver_code = lap_row.get("Driver")
        if not isinstance(driver_code, str) or driver_code not in drivers_map:
            continue
        if not is_valid_lap(lap_row):
            continue

        laps_to_insert.append(
            build_lap(
                session_id=db_session.id,
                driver_id=drivers_map[driver_code].id,
                lap_row=lap_row,
            )
        )

    db.add_all(laps_to_insert)
    db.commit()

    summary = {
        "session_id": db_session.id,
        "session": f"{year} {grand_prix} {session_type}",
        "drivers_count": len(drivers_map),
        "laps_count": len(laps_to_insert),
        "action": action,
    }
    logger.info("Ingesta completada: %s", summary)
    return summary
