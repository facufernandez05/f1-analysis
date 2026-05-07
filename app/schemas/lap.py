# Schemas Pydantic para vueltas.

from pydantic import BaseModel, computed_field


class LapBase(BaseModel):
    lap_number: int
    lap_time_ms: float | None = None
    sector1_ms: float | None = None
    sector2_ms: float | None = None
    sector3_ms: float | None = None
    is_personal_best: bool = False


class LapResponse(LapBase):
    id: int
    session_id: int
    driver_id: int

    # Campo calculado: convierte ms a segundos para facilitar la lectura en el cliente
    @computed_field
    @property
    def lap_time_s(self) -> float | None:
        if self.lap_time_ms is None:
            return None
        return round(self.lap_time_ms / 1000, 3)

    model_config = {"from_attributes": True}
