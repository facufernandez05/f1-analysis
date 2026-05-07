from pydantic import BaseModel, computed_field


class PaceLapPoint(BaseModel):
    lap_number: int
    lap_time_ms: float
    moving_avg_ms: float | None = None
    delta_to_best_ms: float | None = None

    @computed_field  # type: ignore[misc]
    @property
    def lap_time_s(self) -> float:
        return round(self.lap_time_ms / 1000, 3)

    @computed_field  # type: ignore[misc]
    @property
    def moving_avg_s(self) -> float | None:
        if self.moving_avg_ms is None:
            return None
        return round(self.moving_avg_ms / 1000, 3)

    @computed_field  # type: ignore[misc]
    @property
    def delta_to_best_s(self) -> float | None:
        if self.delta_to_best_ms is None:
            return None
        return round(self.delta_to_best_ms / 1000, 3)


class DriverPaceSeries(BaseModel):
    driver_code: str
    driver_name: str
    team: str | None
    laps_count: int
    best_lap_ms: float
    average_lap_ms: float
    laps: list[PaceLapPoint]

    @computed_field  # type: ignore[misc]
    @property
    def best_lap_s(self) -> float:
        return round(self.best_lap_ms / 1000, 3)

    @computed_field  # type: ignore[misc]
    @property
    def average_lap_s(self) -> float:
        return round(self.average_lap_ms / 1000, 3)


class SessionPaceResponse(BaseModel):
    session_id: int
    grand_prix: str
    year: int
    session_type: str
    window_size: int
    normalize_to_best: bool
    session_best_lap_ms: float | None
    drivers: list[DriverPaceSeries]

    @computed_field  # type: ignore[misc]
    @property
    def session_best_lap_s(self) -> float | None:
        if self.session_best_lap_ms is None:
            return None
        return round(self.session_best_lap_ms / 1000, 3)
