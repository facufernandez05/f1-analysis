# Tests de los endpoints de sesiones y pilotos.
#
# Concepto clave — qué testeamos acá:
#   1. Respuesta vacía cuando no hay datos (comportamiento correcto de lista vacía)
#   2. Que los datos insertados en la DB se devuelven correctamente por la API
#   3. Que el 404 funciona cuando el recurso no existe

import pytest

from app.db.models.driver import Driver
from app.db.models.session import F1Session


@pytest.mark.asyncio
async def test_list_sessions_empty(client):
    """Sin datos en la DB, debe devolver lista vacía."""
    response = await client.get("/api/v1/sessions/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_sessions_with_data(client, db):
    """Con una sesión cargada, debe devolverla."""
    session = F1Session(year=2024, grand_prix="Miami", session_type="Q")
    db.add(session)
    db.commit()

    response = await client.get("/api/v1/sessions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["grand_prix"] == "Miami"
    assert data[0]["year"] == 2024
    assert data[0]["session_type"] == "Q"


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    """Buscar una sesión que no existe debe devolver 404."""
    response = await client.get("/api/v1/sessions/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_session_by_id(client, db):
    """Buscar una sesión por ID debe devolver los datos correctos."""
    session = F1Session(year=2024, grand_prix="Monza", session_type="R")
    db.add(session)
    db.commit()
    db.refresh(session)

    response = await client.get(f"/api/v1/sessions/{session.id}")
    assert response.status_code == 200
    assert response.json()["grand_prix"] == "Monza"


@pytest.mark.asyncio
async def test_list_drivers_empty(client):
    response = await client.get("/api/v1/drivers/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_drivers_with_data(client, db):
    driver = Driver(code="COL", full_name="Franco Colapinto", team="Alpine")
    db.add(driver)
    db.commit()

    response = await client.get("/api/v1/drivers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["code"] == "COL"
    assert data[0]["full_name"] == "Franco Colapinto"


@pytest.mark.asyncio
async def test_get_driver_by_code(client, db):
    driver = Driver(code="VER", full_name="Max Verstappen", team="Red Bull")
    db.add(driver)
    db.commit()

    response = await client.get("/api/v1/drivers/VER")
    assert response.status_code == 200
    assert response.json()["full_name"] == "Max Verstappen"


@pytest.mark.asyncio
async def test_get_driver_not_found(client):
    response = await client.get("/api/v1/drivers/ZZZ")
    assert response.status_code == 404
