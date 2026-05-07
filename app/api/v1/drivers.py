# Endpoints de pilotos.

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models.driver import Driver
from app.db.session import get_db
from app.schemas.driver import DriverResponse

router = APIRouter(prefix="/drivers", tags=["drivers"])


@router.get("/", response_model=list[DriverResponse])
def list_drivers(db: Session = Depends(get_db)):
    """Devuelve todos los pilotos cargados."""
    return db.query(Driver).order_by(Driver.code).all()


@router.get("/{driver_code}", response_model=DriverResponse)
def get_driver(driver_code: str, db: Session = Depends(get_db)):
    """Devuelve un piloto por su código (ej: VER, COL, HAM)."""
    driver = db.query(Driver).filter(Driver.code == driver_code.upper()).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver
