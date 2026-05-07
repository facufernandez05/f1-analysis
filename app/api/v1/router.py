# Router central de v1. Agrupa todos los sub-routers.
#
# Concepto clave — APIRouter:
#   En lugar de definir todas las rutas en main.py (que crecería sin control),
#   las separamos por recurso (sessions, drivers, laps) y las incluimos acá.
#   Es el mismo patrón que "Blueprints" en Flask.

from fastapi import APIRouter

from app.api.v1 import drivers, ingest, laps, sessions

router = APIRouter(prefix="/api/v1")

router.include_router(sessions.router)
router.include_router(drivers.router)
router.include_router(laps.router)
router.include_router(ingest.router)
