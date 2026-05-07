import pytest

from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session
from app.services.pace import get_session_pace


def seed_session(db) -> F1Session:
    session = F1Session(year=2026, grand_prix="Bahrain", session_type="R")
    db.add(session)
    db.flush()
    return session


def seed_driver(db, code: str, full_name: str, team: str | None = None) -> Driver:
    driver = Driver(code=code, full_name=full_name, team=team)
    db.add(driver)
    db.flush()
    return driver


def seed_lap(
    db,
    session_id: int,
    driver_id: int,
    lap_number: int,
    lap_time_ms: float,
) -> Lap:
    lap = Lap(
        session_id=session_id,
        driver_id=driver_id,
        lap_number=lap_number,
        lap_time_ms=lap_time_ms,
    )
    db.add(lap)
    db.flush()
    return lap


def test_get_session_pace_not_found(db):
    assert get_session_pace(db, session_id=999) is None


def test_get_session_pace_empty_session(db):
    session = seed_session(db)
    db.commit()

    pace = get_session_pace(db, session.id)

    assert pace is not None
    assert pace.session_id == session.id
    assert pace.drivers == []
    assert pace.session_best_lap_ms is None


def test_get_session_pace_with_data(db):
    session = seed_session(db)
    ver = seed_driver(db, "VER", "Max Verstappen", "Red Bull")
    col = seed_driver(db, "COL", "Franco Colapinto", "Williams")

    seed_lap(db, session.id, ver.id, 1, 100_000.0)
    seed_lap(db, session.id, ver.id, 2, 101_000.0)
    seed_lap(db, session.id, ver.id, 3, 102_000.0)

    seed_lap(db, session.id, col.id, 1, 99_000.0)
    seed_lap(db, session.id, col.id, 2, 100_500.0)
    db.commit()

    pace = get_session_pace(db, session.id, window_size=2, normalize_to_best=True)

    assert pace is not None
    assert pace.session_best_lap_ms == 99_000.0
    assert len(pace.drivers) == 2

    # Ordenado por mejor vuelta (COL primero)
    assert pace.drivers[0].driver_code == "COL"
    assert pace.drivers[0].best_lap_ms == 99_000.0
    assert pace.drivers[1].driver_code == "VER"

    ver_series = next(d for d in pace.drivers if d.driver_code == "VER")
    assert ver_series.laps[0].moving_avg_ms == 100_000.0
    assert ver_series.laps[1].moving_avg_ms == 100_500.0
    assert ver_series.laps[2].moving_avg_ms == 101_500.0
    assert ver_series.laps[0].delta_to_best_ms == 1_000.0
    assert ver_series.laps[2].delta_to_best_ms == 3_000.0


@pytest.mark.asyncio
async def test_pace_endpoint_not_found(client):
    response = await client.get("/api/v1/sessions/999/pace")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pace_endpoint_returns_data(client, db):
    session = seed_session(db)
    ver = seed_driver(db, "VER", "Max Verstappen", "Red Bull")

    seed_lap(db, session.id, ver.id, 1, 90_000.0)
    seed_lap(db, session.id, ver.id, 2, 91_000.0)
    db.commit()

    response = await client.get(
        f"/api/v1/sessions/{session.id}/pace?window_size=2&normalize_to_best=false"
    )
    assert response.status_code == 200

    data = response.json()
    assert data["window_size"] == 2
    assert data["normalize_to_best"] is False
    assert data["session_best_lap_s"] == 90.0
    assert data["drivers"][0]["driver_code"] == "VER"
    assert data["drivers"][0]["laps"][0]["delta_to_best_ms"] is None
