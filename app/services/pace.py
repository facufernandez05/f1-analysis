from collections import defaultdict

from sqlalchemy.orm import Session

from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session
from app.schemas.pace import DriverPaceSeries, PaceLapPoint, SessionPaceResponse


def _moving_average(values: list[float], window_size: int) -> list[float]:
    result: list[float] = []
    for idx in range(len(values)):
        start = max(0, idx - window_size + 1)
        chunk = values[start : idx + 1]
        result.append(sum(chunk) / len(chunk))
    return result


def get_session_pace(
    db: Session,
    session_id: int,
    window_size: int = 3,
    normalize_to_best: bool = True,
) -> SessionPaceResponse | None:
    f1_session = db.get(F1Session, session_id)
    if f1_session is None:
        return None

    rows = (
        db.query(Lap, Driver)
        .join(Driver, Lap.driver_id == Driver.id)
        .filter(Lap.session_id == session_id)
        .filter(Lap.lap_time_ms.isnot(None))
        .order_by(Driver.code.asc(), Lap.lap_number.asc())
        .all()
    )

    if not rows:
        return SessionPaceResponse(
            session_id=f1_session.id,
            grand_prix=f1_session.grand_prix,
            year=f1_session.year,
            session_type=f1_session.session_type,
            window_size=window_size,
            normalize_to_best=normalize_to_best,
            session_best_lap_ms=None,
            drivers=[],
        )

    grouped: dict[str, list[tuple[Lap, Driver]]] = defaultdict(list)
    session_best_lap_ms = min(lap.lap_time_ms for lap, _ in rows)

    for lap, driver in rows:
        grouped[driver.code].append((lap, driver))

    driver_series: list[DriverPaceSeries] = []

    for code in sorted(grouped.keys()):
        driver_rows = grouped[code]
        _, driver = driver_rows[0]

        lap_times = [lap.lap_time_ms for lap, _ in driver_rows]
        moving_avgs = _moving_average(lap_times, window_size)
        best_lap_ms = min(lap_times)

        pace_points: list[PaceLapPoint] = []
        for idx, (lap, _) in enumerate(driver_rows):
            delta = None
            if normalize_to_best:
                delta = lap.lap_time_ms - session_best_lap_ms

            pace_points.append(
                PaceLapPoint(
                    lap_number=lap.lap_number,
                    lap_time_ms=lap.lap_time_ms,
                    moving_avg_ms=round(moving_avgs[idx], 3),
                    delta_to_best_ms=round(delta, 3) if delta is not None else None,
                )
            )

        driver_series.append(
            DriverPaceSeries(
                driver_code=driver.code,
                driver_name=driver.full_name,
                team=driver.team,
                laps_count=len(lap_times),
                best_lap_ms=best_lap_ms,
                average_lap_ms=round(sum(lap_times) / len(lap_times), 3),
                laps=pace_points,
            )
        )

    driver_series.sort(key=lambda d: d.best_lap_ms)

    return SessionPaceResponse(
        session_id=f1_session.id,
        grand_prix=f1_session.grand_prix,
        year=f1_session.year,
        session_type=f1_session.session_type,
        window_size=window_size,
        normalize_to_best=normalize_to_best,
        session_best_lap_ms=session_best_lap_ms,
        drivers=driver_series,
    )
