# Schemas Pydantic para sesiones F1.
#
# Concepto clave — ¿Por qué schemas separados de los modelos?
#   Los modelos SQLAlchemy representan la tabla en la DB.
#   Los schemas Pydantic representan lo que la API recibe/devuelve (JSON).
#   Separarlos evita exponer datos internos y permite validar la entrada.
#
#   Ejemplo: el modelo tiene "laps" (lista de vueltas), pero en GET /sessions
#   no queremos devolver todas las vueltas embebidas — solo los datos de la sesión.

from datetime import date

from pydantic import BaseModel


class SessionBase(BaseModel):
    year: int
    grand_prix: str
    session_type: str
    session_date: date | None = None


class SessionCreate(SessionBase):
    """Schema para crear una sesión (POST). Por ahora no se usa, viene en iter. 3."""

    pass


class SessionResponse(SessionBase):
    """Schema de respuesta. Lo que devuelve GET /sessions."""

    id: int

    # from_attributes=True permite que Pydantic lea desde objetos SQLAlchemy
    # (en lugar de solo diccionarios). Sin esto, model_validate() falla.
    model_config = {"from_attributes": True}
