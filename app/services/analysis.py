# Lógica de análisis de sesiones.
#
# Concepto clave — agregaciones con SQLAlchemy:
#   En lugar de traer todos los registros a Python y calcular con listas,
#   usamos func.min(), func.avg(), func.count() para delegar el cálculo
#   al motor de DB. Esto escala bien: si hay 1000 vueltas, el JOIN y el
#   GROUP BY los hace Postgres (o SQLite en tests), no Python.

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session
from app.schemas.stats import DriverRankingEntry, FastestLapInfo, SessionStats


def get_session_stats(db: Session, session_id: int) -> SessionStats | None:
    """
    Calcula estadísticas agregadas de una sesión.

    Retorna None si la sesión no existe.
    Si existe pero no tiene vueltas, devuelve el objeto con listas vacías y Nones.
    """
    # 1. Verificar que la sesión existe
    f1_session = db.get(F1Session, session_id)
    if f1_session is None:
        return None

    # 2. Vuelta más rápida (JOIN con Driver para tener el nombre)
    fastest_row = (
        db.query(Lap, Driver)
        .join(Driver, Lap.driver_id == Driver.id)
        .filter(Lap.session_id == session_id)
        .filter(Lap.lap_time_ms.isnot(None))
        .order_by(Lap.lap_time_ms.asc())
        .first()
    )

    fastest_lap_info: FastestLapInfo | None = None
    if fastest_row is not None:
        fastest_lap, fastest_driver = fastest_row
        fastest_lap_info = FastestLapInfo(
            driver_code=fastest_driver.code,
            driver_name=fastest_driver.full_name,
            team=fastest_driver.team,
            lap_number=fastest_lap.lap_number,
            lap_time_ms=fastest_lap.lap_time_ms,
        )

    # 3. Promedio global de lap_time_ms (solo vueltas válidas)
    avg_ms: float | None = (
        db.query(func.avg(Lap.lap_time_ms))
        .filter(
            Lap.session_id == session_id,
            Lap.lap_time_ms.isnot(None),
        )
        .scalar()
    )
    if avg_ms is not None:
        avg_ms = round(float(avg_ms), 3)

    # 4. Total de vueltas válidas
    total_laps: int = (
        db.query(func.count(Lap.id))
        .filter(Lap.session_id == session_id, Lap.lap_time_ms.isnot(None))
        .scalar()
        or 0
    )

    # 5. Ranking por piloto: mejor vuelta y cantidad de vueltas válidas
    #    GROUP BY Driver.id para obtener un registro por piloto
    ranking_rows = (
        db.query(
            Driver.code,
            Driver.full_name,
            Driver.team,
            func.min(Lap.lap_time_ms).label("best_lap_time_ms"),
            func.count(Lap.id).label("total_laps"),
        )
        .join(Lap, Lap.driver_id == Driver.id)
        .filter(Lap.session_id == session_id)
        .filter(Lap.lap_time_ms.isnot(None))
        .group_by(Driver.id, Driver.code, Driver.full_name, Driver.team)
        .order_by(func.min(Lap.lap_time_ms).asc())
        .all()
    )

    driver_rankings = [
        DriverRankingEntry(
            rank=idx + 1,
            driver_code=row.code,
            driver_name=row.full_name,
            team=row.team,
            best_lap_time_ms=row.best_lap_time_ms,
            total_laps=row.total_laps,
        )
        for idx, row in enumerate(ranking_rows)
    ]

    return SessionStats(
        session_id=f1_session.id,
        grand_prix=f1_session.grand_prix,
        year=f1_session.year,
        session_type=f1_session.session_type,
        total_laps=total_laps,
        fastest_lap=fastest_lap_info,
        average_lap_time_ms=avg_ms,
        driver_rankings=driver_rankings,
    )
