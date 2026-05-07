# Endpoint de ingesta de datos desde fastf1.
#
# Concepto clave — separación de responsabilidades:
#   Este archivo solo maneja HTTP: recibe el request, llama al servicio,
#   y transforma el resultado en una respuesta HTTP apropiada.
#   Toda la lógica real vive en app/services/ingestion.py.
#
# Concepto clave — 502 Bad Gateway:
#   Cuando nuestro servidor llama a un servicio externo (fastf1 → ergast API)
#   y ese servicio falla, el código correcto es 502 (nosotros somos el gateway
#   hacia fastf1). 404 sería si el recurso no existe en *nuestra* API.

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db
from app.schemas.ingest import IngestRequest, IngestResponse
from app.services.ingestion import ingest_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/", response_model=IngestResponse, status_code=201)
def trigger_ingest(body: IngestRequest, db: Session = Depends(get_db)):
    """
    Dispara la importación de una sesión desde fastf1.

    - Si la sesión ya existe, borra las vueltas anteriores y las re-importa.
    - Requiere conectividad a internet (fastf1 descarga datos de la API de F1).
    - La caché local (FASTF1_CACHE_PATH) evita re-descargar en llamadas repetidas.
    """
    try:
        summary = ingest_session(
            db=db,
            year=body.year,
            grand_prix=body.grand_prix,
            session_type=body.session_type,
            cache_path=settings.FASTF1_CACHE_PATH,
        )
    except Exception as exc:
        logger.exception(
            "Error al ingestar sesión %s %s %s",
            body.year,
            body.grand_prix,
            body.session_type,
        )
        raise HTTPException(
            status_code=502,
            detail=f"Error al obtener datos de fastf1: {exc}",
        ) from exc

    return IngestResponse(**summary)
