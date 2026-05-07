# Tests del endpoint POST /api/v1/ingest.
#
# Concepto clave — mockear en el punto de uso:
#   Parchamos "app.api.v1.ingest.ingest_session" (donde SE IMPORTA la función)
#   y no "app.services.ingestion.ingest_session" (donde SE DEFINE).
#   Así el endpoint recibe el mock transparentemente.

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_ingest_success(client):
    """POST /ingest con datos válidos → 201 y resumen de ingesta."""
    mock_summary = {
        "session_id": 1,
        "session": "2026 Bahrain R",
        "drivers_count": 20,
        "laps_count": 1100,
        "action": "created",
    }

    with patch("app.api.v1.ingest.ingest_session", return_value=mock_summary):
        response = await client.post(
            "/api/v1/ingest/",
            json={"year": 2026, "grand_prix": "Bahrain", "session_type": "R"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == 1
    assert data["session"] == "2026 Bahrain R"
    assert data["drivers_count"] == 20
    assert data["laps_count"] == 1100
    assert data["action"] == "created"


@pytest.mark.asyncio
async def test_ingest_reimport(client):
    """Si la sesión ya existe, action debe ser 'reimported'."""
    mock_summary = {
        "session_id": 5,
        "session": "2026 Monaco Q",
        "drivers_count": 20,
        "laps_count": 300,
        "action": "reimported",
    }

    with patch("app.api.v1.ingest.ingest_session", return_value=mock_summary):
        response = await client.post(
            "/api/v1/ingest/",
            json={"year": 2026, "grand_prix": "Monaco", "session_type": "Q"},
        )

    assert response.status_code == 201
    assert response.json()["action"] == "reimported"


@pytest.mark.asyncio
async def test_ingest_fastf1_error_returns_502(client):
    """Si fastf1 lanza una excepción, el endpoint debe devolver 502."""
    with patch(
        "app.api.v1.ingest.ingest_session",
        side_effect=RuntimeError("fastf1 network error"),
    ):
        response = await client.post(
            "/api/v1/ingest/",
            json={"year": 2026, "grand_prix": "Bahrain", "session_type": "R"},
        )

    assert response.status_code == 502
    assert "fastf1" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ingest_invalid_session_type(client):
    """session_type fuera del Literal válido → 422 Unprocessable Entity."""
    response = await client.post(
        "/api/v1/ingest/",
        json={"year": 2026, "grand_prix": "Bahrain", "session_type": "INVALID"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_year_out_of_range(client):
    """year < 2018 → 422 Unprocessable Entity (Field ge=2018)."""
    response = await client.post(
        "/api/v1/ingest/",
        json={"year": 2000, "grand_prix": "Bahrain", "session_type": "R"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_missing_fields(client):
    """Request sin campos obligatorios → 422."""
    response = await client.post("/api/v1/ingest/", json={})
    assert response.status_code == 422
