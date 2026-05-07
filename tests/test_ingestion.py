# Tests del servicio de ingesta.
#
# Concepto clave — Mocking:
#   Los tests unitarios deben ser rápidos, predecibles y sin efectos secundarios.
#   fastf1 hace requests HTTP y lee archivos del disco → no queremos eso en tests.
#
#   Con unittest.mock.patch reemplazamos temporalmente fastf1.get_session() con
#   un objeto falso (MagicMock) que devuelve datos controlados por nosotros.
#   El código bajo test no sabe que está usando un mock — solo ve el mismo API.
#
#   Sintaxis:
#     @patch("app.services.ingestion.fastf1")   ← parchea el módulo donde SE USA
#     def test_algo(mock_fastf1):                ← el mock se inyecta como argumento
#         mock_fastf1.get_session.return_value = ...

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session
from app.services.ingestion import (
    build_lap,
    get_or_create_driver,
    ingest_session,
    is_valid_lap,
    timedelta_to_ms,
)

# ---------------------------------------------------------------------------
# Setup de la DB de test (SQLite en memoria, igual que en conftest.py)
# ---------------------------------------------------------------------------

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helper: construye un mock de sesión fastf1 con datos controlados
# ---------------------------------------------------------------------------


def make_mock_ff1_session(include_invalid_lap: bool = False) -> MagicMock:
    """
    Devuelve un MagicMock que simula una sesión de fastf1.
    Tiene 2 pilotos (VER y COL) con 2 vueltas cada uno.
    """
    mock_session = MagicMock()
    mock_session.date = pd.Timestamp("2024-05-04 15:00:00")

    rows = [
        {
            "Driver": "VER",
            "LapNumber": 1.0,
            "LapTime": pd.Timedelta(seconds=80.500),
            "Sector1Time": pd.Timedelta(seconds=25.0),
            "Sector2Time": pd.Timedelta(seconds=30.0),
            "Sector3Time": pd.Timedelta(seconds=25.5),
            "IsPersonalBest": False,
        },
        {
            "Driver": "VER",
            "LapNumber": 2.0,
            "LapTime": pd.Timedelta(seconds=79.123),
            "Sector1Time": pd.Timedelta(seconds=24.5),
            "Sector2Time": pd.Timedelta(seconds=29.8),
            "Sector3Time": pd.Timedelta(seconds=24.823),
            "IsPersonalBest": True,
        },
        {
            "Driver": "COL",
            "LapNumber": 1.0,
            "LapTime": pd.Timedelta(seconds=81.000),
            "Sector1Time": pd.Timedelta(seconds=26.0),
            "Sector2Time": pd.Timedelta(seconds=30.5),
            "Sector3Time": pd.Timedelta(seconds=24.5),
            "IsPersonalBest": False,
        },
        {
            "Driver": "COL",
            "LapNumber": 2.0,
            "LapTime": pd.Timedelta(seconds=80.200),
            "Sector1Time": pd.Timedelta(seconds=25.5),
            "Sector2Time": pd.Timedelta(seconds=30.0),
            "Sector3Time": pd.Timedelta(seconds=24.7),
            "IsPersonalBest": True,
        },
    ]

    if include_invalid_lap:
        # Vuelta sin LapTime (típico in-lap o out-lap)
        rows.append(
            {
                "Driver": "VER",
                "LapNumber": 3.0,
                "LapTime": pd.NaT,
                "Sector1Time": pd.NaT,
                "Sector2Time": pd.NaT,
                "Sector3Time": pd.NaT,
                "IsPersonalBest": False,
            }
        )

    mock_session.laps = pd.DataFrame(rows)

    drivers_info = {
        "VER": {"FullName": "Max Verstappen", "TeamName": "Red Bull Racing"},
        "COL": {"FullName": "Franco Colapinto", "TeamName": "Alpine"},
    }
    # get_driver() devuelve un dict-like, simulado con un dict real
    mock_session.get_driver = lambda code: drivers_info.get(code, {})

    return mock_session


# ---------------------------------------------------------------------------
# Tests de funciones puras
# ---------------------------------------------------------------------------


def test_timedelta_to_ms_conversion():
    """Convierte correctamente a milisegundos."""
    td = pd.Timedelta(seconds=80.5)
    assert timedelta_to_ms(td) == pytest.approx(80500.0)


def test_timedelta_to_ms_nat_returns_none():
    """NaT (Not a Time) debe devolver None."""
    assert timedelta_to_ms(pd.NaT) is None


def test_timedelta_to_ms_none_returns_none():
    assert timedelta_to_ms(None) is None


def test_is_valid_lap_with_valid_data():
    row = pd.Series({"LapTime": pd.Timedelta(seconds=80.0), "LapNumber": 1.0})
    assert is_valid_lap(row) is True


def test_is_valid_lap_missing_lap_time():
    """Vueltas sin tiempo no son válidas (in-laps, out-laps)."""
    row = pd.Series({"LapTime": pd.NaT, "LapNumber": 1.0})
    assert is_valid_lap(row) is False


# ---------------------------------------------------------------------------
# Tests de funciones de DB
# ---------------------------------------------------------------------------


def test_get_or_create_driver_creates_new(db):
    """Crea un piloto si no existe."""
    driver = get_or_create_driver(db, "VER", "Max Verstappen", "Red Bull Racing")
    db.commit()

    assert driver.id is not None
    assert driver.code == "VER"
    assert driver.full_name == "Max Verstappen"


def test_get_or_create_driver_returns_existing(db):
    """Reutiliza el piloto existente en lugar de crear uno duplicado."""
    driver1 = get_or_create_driver(db, "HAM", "Lewis Hamilton", "Mercedes")
    db.commit()

    driver2 = get_or_create_driver(db, "HAM", "Lewis Hamilton", "Ferrari")
    db.commit()

    # Mismo objeto en DB, equipo actualizado
    assert driver1.id == driver2.id
    assert driver2.team == "Ferrari"
    assert db.query(Driver).filter(Driver.code == "HAM").count() == 1


def test_build_lap():
    """build_lap construye un objeto Lap con los valores correctos."""
    row = pd.Series(
        {
            "LapNumber": 2.0,
            "LapTime": pd.Timedelta(seconds=79.123),
            "Sector1Time": pd.Timedelta(seconds=24.5),
            "Sector2Time": pd.Timedelta(seconds=29.8),
            "Sector3Time": pd.Timedelta(seconds=24.823),
            "IsPersonalBest": True,
        }
    )
    lap = build_lap(session_id=1, driver_id=5, lap_row=row)

    assert lap.lap_number == 2
    assert lap.session_id == 1
    assert lap.driver_id == 5
    assert lap.lap_time_ms == pytest.approx(79123.0)
    assert lap.is_personal_best is True


# ---------------------------------------------------------------------------
# Tests del flujo completo con fastf1 mockeado
# ---------------------------------------------------------------------------


@patch("app.services.ingestion.fastf1")
def test_ingest_session_creates_records(mock_fastf1, db):
    """
    El flujo completo crea la sesión, los pilotos y las vueltas en DB.
    fastf1 está mockeado: no hay red ni archivos reales.
    """
    mock_fastf1.get_session.return_value = make_mock_ff1_session()

    result = ingest_session(db, year=2024, grand_prix="Miami", session_type="Q")

    assert result["drivers_count"] == 2
    assert result["laps_count"] == 4
    assert result["action"] == "creada"

    # Verificar que se crearon realmente en DB
    assert db.query(F1Session).count() == 1
    assert db.query(Driver).count() == 2
    assert db.query(Lap).count() == 4


@patch("app.services.ingestion.fastf1")
def test_ingest_session_filters_invalid_laps(mock_fastf1, db):
    """Las vueltas sin LapTime (in-laps/out-laps) deben ignorarse."""
    mock_fastf1.get_session.return_value = make_mock_ff1_session(
        include_invalid_lap=True
    )

    result = ingest_session(db, year=2024, grand_prix="Miami", session_type="Q")

    # 4 vueltas válidas + 1 inválida → solo 4 insertadas
    assert result["laps_count"] == 4
    assert db.query(Lap).count() == 4


@patch("app.services.ingestion.fastf1")
def test_ingest_session_is_idempotent(mock_fastf1, db):
    """
    Correr la ingesta dos veces para la misma sesión no duplica datos.
    La segunda corrida reemplaza las vueltas (borra y re-inserta).
    """
    mock_fastf1.get_session.return_value = make_mock_ff1_session()

    result1 = ingest_session(db, year=2024, grand_prix="Miami", session_type="Q")
    result2 = ingest_session(db, year=2024, grand_prix="Miami", session_type="Q")

    assert result1["action"] == "creada"
    assert result2["action"] == "actualizada"

    # Después de 2 corridas debe haber exactamente 1 sesión y 4 vueltas
    assert db.query(F1Session).count() == 1
    assert db.query(Lap).count() == 4
    assert db.query(Driver).count() == 2


@patch("app.services.ingestion.fastf1")
def test_ingest_two_different_sessions(mock_fastf1, db):
    """Ingestar dos sesiones distintas crea dos registros separados."""
    mock_fastf1.get_session.return_value = make_mock_ff1_session()

    ingest_session(db, year=2024, grand_prix="Miami", session_type="Q")
    ingest_session(db, year=2024, grand_prix="Miami", session_type="R")

    assert db.query(F1Session).count() == 2
    assert db.query(Lap).count() == 8  # 4 vueltas por sesión
