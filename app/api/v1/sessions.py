# Endpoints de sesiones F1.
#
# Concepto clave — Depends():
#   FastAPI tiene un sistema de inyección de dependencias.
#   "db: Session = Depends(get_db)" le dice a FastAPI:
#     "antes de ejecutar este endpoint, llamá get_db() y pasame el resultado".
#   Esto hace que la sesión de DB se cree y se cierre automáticamente
#   por cada request, sin que el endpoint se tenga que preocupar.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.session import F1Session
from app.db.session import get_db
from app.schemas.session import SessionResponse
from app.schemas.stats import SessionStats
from app.services.analysis import get_session_stats

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
