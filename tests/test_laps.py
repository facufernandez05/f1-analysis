# Tests del endpoint de vueltas.

import pytest

from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session


@pytest.fixture
def seed_data(db):
    """Inserta una sesión, un piloto y 3 vueltas en la DB de test."""
    session = F1Session(year=2024, grand_prix="Silverstone", session_type="Q")
    driver = Driver(code="HAM", full_name="Lewis Hamilton", team="Mercedes")
    db.add_all([session, driver])
    db.commit()
    db.refresh(session)
    db.refresh(driver)

    laps = [
        Lap(
            session_id=session.id,
            driver_id=driver.id,
            lap_number=i,
            lap_time_ms=80000 + i * 100,
            sector1_ms=25000,
            sector2_ms=30000,
            sector3_ms=25000 + i * 100,
        )
        for i in range(1, 4)
    ]
    db.add_all(laps)
    db.commit()

    return {"session": session, "driver": driver}


@pytest.mark.asyncio
async def test_list_laps(client, seed_data):
    """Debe devolver las 3 vueltas de la sesión."""
    session_id = seed_data["session"].id
    response = await client.get(f"/api/v1/sessions/{session_id}/laps")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    # Verifica que el campo calculado lap_time_s está presente
    assert "lap_time_s" in data[0]
    assert data[0]["lap_time_s"] == round(80100 / 1000, 3)


@pytest.mark.asyncio
async def test_list_laps_filter_by_driver(client, seed_data):
    """Filtrar por driver_code=HAM debe devolver las mismas 3 vueltas."""
    session_id = seed_data["session"].id
    response = await client.get(f"/api/v1/sessions/{session_id}/laps?driver_code=HAM")
    assert response.status_code == 200
    assert len(response.json()) == 3


@pytest.mark.asyncio
async def test_list_laps_session_not_found(client):
    response = await client.get("/api/v1/sessions/999/laps")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_laps_driver_not_found(client, seed_data):
    session_id = seed_data["session"].id
    response = await client.get(f"/api/v1/sessions/{session_id}/laps?driver_code=ZZZ")
    assert response.status_code == 404
