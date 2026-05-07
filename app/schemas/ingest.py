# Schemas para el endpoint de ingesta.
#
# Concepto clave — Literal types:
#   En lugar de validar con regex o código manual, Pydantic acepta un tipo
#   Literal["R", "Q", ...] que automáticamente rechaza cualquier valor fuera
#   de la lista y lo documenta en el OpenAPI schema generado.

from typing import Literal

from pydantic import BaseModel, Field

# Tipos de sesión válidos en fastf1
SessionTypeLiteral = Literal["R", "Q", "S", "SS", "FP1", "FP2", "FP3"]


class IngestRequest(BaseModel):
    """Cuerpo del POST /ingest. Identifica la sesión a importar desde fastf1."""

    year: int = Field(..., ge=2018, le=2030, description="Año del campeonato")
    grand_prix: str = Field(
        ..., min_length=1, description="Nombre del GP, ej: 'Bahrain'"
    )
    session_type: SessionTypeLiteral = Field(
        ..., description="Tipo de sesión: R=Carrera, Q=Clasificación, FP1-3=Práctica"
    )


class IngestResponse(BaseModel):
    """Respuesta del POST /ingest con un resumen de lo que se importó."""

    session_id: int
    session: str  # "2026 Bahrain R"
    drivers_count: int
    laps_count: int
    action: Literal["created", "reimported"]
