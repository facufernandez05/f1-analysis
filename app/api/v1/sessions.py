# Endpoints de sesiones F1.
#
# Concepto clave — Depends():
#   FastAPI tiene un sistema de inyección de dependencias.
#   "db: Session = Depends(get_db)" le dice a FastAPI:
#     "antes de ejecutar este endpoint, llamá get_db() y pasame el resultado".
#   Esto hace que la sesión de DB se cree y se cierre automáticamente
#   por cada request, sin que el endpoint se tenga que preocupar.

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models.session import F1Session
from app.db.session import get_db
from app.schemas.pace import SessionPaceResponse
from app.schemas.session import SessionResponse
from app.schemas.stats import SessionStats
from app.services.analysis import get_session_stats
from app.services.pace import get_session_pace

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/", response_model=list[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    """Devuelve todas las sesiones cargadas en la base de datos."""
    return db.query(F1Session).order_by(F1Session.year.desc()).all()


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Devuelve una sesión por ID. Devuelve 404 si no existe."""
    session = db.query(F1Session).filter(F1Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/{session_id}/stats", response_model=SessionStats)
def get_stats(session_id: int, db: Session = Depends(get_db)):
    """
    Devuelve estadísticas agregadas de una sesión:
    vuelta más rápida, tiempo promedio y ranking de pilotos por mejor vuelta.
    """
    stats = get_session_stats(db, session_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return stats


@router.get("/{session_id}/pace", response_model=SessionPaceResponse)
def get_pace(
    session_id: int,
    window_size: int = Query(default=3, ge=1, le=10),
    normalize_to_best: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """
    Devuelve series de pace por piloto, incluyendo moving average por vuelta.

    - window_size: tamaño de la ventana para promedio móvil
    - normalize_to_best: si true, agrega delta por vuelta vs mejor vuelta de sesión
    """
    pace = get_session_pace(
        db,
        session_id,
        window_size=window_size,
        normalize_to_best=normalize_to_best,
    )
    if pace is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return pace
