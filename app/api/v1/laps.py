# Endpoints de vueltas.
#
# Concepto clave — Query params vs Path params:
#   Path param:  /sessions/5/laps        → session_id=5 va en la URL
#   Query param: /sessions/5/laps?driver_code=VER → driver_code va después del ?
#   Los query params son opcionales por defecto si tienen valor por defecto (None).

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.driver import Driver
from app.db.models.lap import Lap
from app.db.models.session import F1Session
from app.db.session import get_db
from app.schemas.lap import LapResponse

router = APIRouter(prefix="/sessions", tags=["laps"])


@router.get("/{session_id}/laps", response_model=list[LapResponse])
def list_laps(
    session_id: int,
    driver_code: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Devuelve las vueltas de una sesión.
    Opcionalmente filtrá por piloto: GET /sessions/1/laps?driver_code=VER
    """
    # Verificar que la sesión existe
    session = db.query(F1Session).filter(F1Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    query = db.query(Lap).filter(Lap.session_id == session_id)

    if driver_code:
        driver = db.query(Driver).filter(Driver.code == driver_code.upper()).first()
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        query = query.filter(Lap.driver_id == driver.id)

    return query.order_by(Lap.lap_number).all()
