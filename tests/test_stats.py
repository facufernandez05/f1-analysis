# Tests del endpoint GET /api/v1/sessions/{id}/stats
# y del servicio get_session_stats directamente.
#
# Concepto clave — seed de datos en tests:
#   Para testear estadísticas necesitamos datos reales en la DB de test.
#   No mockeamos la DB: creamos sesiones, pilotos y vueltas directamente
#   con el ORM y verificamos que las consultas SQL devuelven los resultados
#   esperados. Así también testeamos que nuestras queries SQL son correctas.

import pytest

from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session
from app.services.analysis import get_session_stats

# ---------------------------------------------------------------------------
# Helpers para sembrar datos de prueba
# ---------------------------------------------------------------------------


def seed_session(db) -> F1Session:
    """Crea una sesión de prueba."""
    s = F1Session(year=2026, grand_prix="Bahrain", session_type="R")
    db.add(s)
    db.flush()
    return s


def seed_driver(db, code: str, full_name: str, team: str | None = None) -> Driver:
    """Crea un piloto de prueba."""
    d = Driver(code=code, full_name=full_name, team=team)
    db.add(d)
    db.flush()
    return d


def seed_lap(
    db,
    session_id: int,
    driver_id: int,
    lap_number: int,
    lap_time_ms: float | None,
) -> Lap:
    """Crea una vuelta de prueba."""
    lap = Lap(
        session_id=session_id,
        driver_id=driver_id,
        lap_number=lap_number,
        lap_time_ms=lap_time_ms,
    )
    db.add(lap)
    db.flush()
    return lap


# ---------------------------------------------------------------------------
# Tests del servicio (sin HTTP, con DB real de test)
# ---------------------------------------------------------------------------


def test_get_session_stats_returns_none_for_missing_session(db):
    """Devuelve None si la sesión no existe."""
    assert get_session_stats(db, session_id=999) is None


def test_get_session_stats_no_laps(db):
    """Una sesión sin vueltas devuelve stats vacías (no None)."""
    s = seed_session(db)
    db.commit()

    stats = get_session_stats(db, s.id)

    assert stats is not None
    assert stats.session_id == s.id
    assert stats.total_laps == 0
    assert stats.fastest_lap is None
    assert stats.average_lap_time_ms is None
    assert stats.average_lap_time_s is None
    assert stats.driver_rankings == []


def test_get_session_stats_with_laps(db):
    """Estadísticas correctas con dos pilotos y varias vueltas."""
    s = seed_session(db)
    ver = seed_driver(db, "VER", "Max Verstappen", "Red Bull")
    col = seed_driver(db, "COL", "Franco Colapinto", "Williams")

    # VER: 90s, 91s, 92s — mejor: 90000ms
    seed_lap(db, s.id, ver.id, 1, 90_000.0)
    seed_lap(db, s.id, ver.id, 2, 91_000.0)
    seed_lap(db, s.id, ver.id, 3, 92_000.0)

    # COL: 93s, 94s — mejor: 93000ms
    seed_lap(db, s.id, col.id, 1, 93_000.0)
    seed_lap(db, s.id, col.id, 2, 94_000.0)
    db.commit()

    stats = get_session_stats(db, s.id)

    assert stats is not None
    assert stats.total_laps == 5

    # Vuelta más rápida: VER, vuelta 1, 90s
    assert stats.fastest_lap is not None
    assert stats.fastest_lap.driver_code == "VER"
    assert stats.fastest_lap.lap_number == 1
    assert stats.fastest_lap.lap_time_ms == 90_000.0
    assert stats.fastest_lap.lap_time_s == 90.0

    # Promedio: (90+91+92+93+94)/5 * 1000 = 92000ms
    assert stats.average_lap_time_ms == 92_000.0
    assert stats.average_lap_time_s == 92.0

    # Ranking: VER primero (90s), COL segundo (93s)
    assert len(stats.driver_rankings) == 2
    assert stats.driver_rankings[0].rank == 1
    assert stats.driver_rankings[0].driver_code == "VER"
    assert stats.driver_rankings[0].best_lap_time_ms == 90_000.0
    assert stats.driver_rankings[0].best_lap_time_s == 90.0
    assert stats.driver_rankings[0].total_laps == 3

    assert stats.driver_rankings[1].rank == 2
    assert stats.driver_rankings[1].driver_code == "COL"
    assert stats.driver_rankings[1].total_laps == 2


def test_get_session_stats_ignores_null_lap_times(db):
    """Las vueltas con lap_time_ms=None no se cuentan en las estadísticas."""
    s = seed_session(db)
    ver = seed_driver(db, "VER", "Max Verstappen", "Red Bull")

    seed_lap(db, s.id, ver.id, 1, 90_000.0)
    seed_lap(db, s.id, ver.id, 2, None)  # vuelta inválida (entrada a pits, etc.)
    db.commit()

    stats = get_session_stats(db, s.id)

    assert stats is not None
    assert stats.total_laps == 1  # solo la vuelta válida
    assert stats.fastest_lap.lap_time_ms == 90_000.0


# ---------------------------------------------------------------------------
# Tests del endpoint HTTP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stats_endpoint_not_found(client):
    """GET /sessions/999/stats devuelve 404 si la sesión no existe."""
    response = await client.get("/api/v1/sessions/999/stats")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stats_endpoint_returns_data(client, db):
    """GET /sessions/{id}/stats devuelve el JSON correcto con datos."""
    # Seed data directamente en la DB de test del fixture
    s = seed_session(db)
    ver = seed_driver(db, "VER", "Max Verstappen", "Red Bull")
    col = seed_driver(db, "COL", "Franco Colapinto", "Williams")

    seed_lap(db, s.id, ver.id, 1, 88_000.0)
    seed_lap(db, s.id, col.id, 1, 90_000.0)
    db.commit()

    response = await client.get(f"/api/v1/sessions/{s.id}/stats")

    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] == s.id
    assert data["grand_prix"] == "Bahrain"
    assert data["year"] == 2026
    assert data["total_laps"] == 2

    # Computed field lap_time_s
    assert data["fastest_lap"]["driver_code"] == "VER"
    assert data["fastest_lap"]["lap_time_s"] == 88.0

    # Ranking
    assert data["driver_rankings"][0]["driver_code"] == "VER"
    assert data["driver_rankings"][1]["driver_code"] == "COL"
    assert data["driver_rankings"][0]["best_lap_time_s"] == 88.0


@pytest.mark.asyncio
async def test_stats_endpoint_empty_session(client, db):
    """Una sesión sin vueltas devuelve 200 con listas vacías."""
    s = seed_session(db)
    db.commit()

    response = await client.get(f"/api/v1/sessions/{s.id}/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["total_laps"] == 0
    assert data["fastest_lap"] is None
    assert data["average_lap_time_ms"] is None
    assert data["driver_rankings"] == []
