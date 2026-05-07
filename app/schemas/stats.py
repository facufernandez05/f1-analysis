# Schemas para el endpoint de estadísticas de sesión.
#
# Concepto clave — modelos anidados:
#   Pydantic permite anidar schemas (un modelo dentro de otro).
#   Acá SessionStats contiene FastestLapInfo y una lista de DriverRankingEntry.
#   FastAPI serializa todo esto a JSON automáticamente.

from pydantic import BaseModel, computed_field


class FastestLapInfo(BaseModel):
    """La vuelta más rápida de la sesión."""

    driver_code: str
    driver_name: str
    team: str | None
    lap_number: int
    lap_time_ms: float

    @computed_field  # type: ignore[misc]
    @property
    def lap_time_s(self) -> float:
        """Tiempo en segundos, redondeado a 3 decimales."""
        return round(self.lap_time_ms / 1000, 3)


class DriverRankingEntry(BaseModel):
    """Posición de un piloto en el ranking de la sesión (por mejor vuelta)."""

    rank: int
    driver_code: str
    driver_name: str
    team: str | None
    best_lap_time_ms: float
    total_laps: int

    @computed_field  # type: ignore[misc]
    @property
    def best_lap_time_s(self) -> float:
        """Mejor tiempo en segundos, redondeado a 3 decimales."""
        return round(self.best_lap_time_ms / 1000, 3)


class SessionStats(BaseModel):
    """Estadísticas agregadas de una sesión."""

    session_id: int
    grand_prix: str
    year: int
    session_type: str
    total_laps: int
    fastest_lap: FastestLapInfo | None
    average_lap_time_ms: float | None

    @computed_field  # type: ignore[misc]
    @property
    def average_lap_time_s(self) -> float | None:
        """Tiempo promedio en segundos."""
        if self.average_lap_time_ms is None:
            return None
        return round(self.average_lap_time_ms / 1000, 3)

    driver_rankings: list[DriverRankingEntry]
