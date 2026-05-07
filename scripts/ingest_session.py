#!/usr/bin/env python3
"""
Script CLI para ingestar una sesión de F1 en la base de datos.

Uso:
    python scripts/ingest_session.py --year 2024 --gp Miami --session Q
    python scripts/ingest_session.py --year 2024 --gp Monza --session R
    python scripts/ingest_session.py --year 2026 --gp Miami --session Q --cache data/

Requiere que la base de datos esté corriendo:
    docker compose -f docker-compose.dev.yml up -d db
    alembic upgrade head
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

# Agrega la raíz del proyecto al path para poder importar app.*
# Esto es necesario cuando el script se ejecuta directamente con python.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.services.ingestion import ingest_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

VALID_SESSION_TYPES = {"Q", "R", "FP1", "FP2", "FP3", "S", "SQ", "SS"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingestar una sesión de F1 en la base de datos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scripts/ingest_session.py --year 2024 --gp Miami --session Q
  python scripts/ingest_session.py --year 2024 --gp "São Paulo" --session R
        """,
    )
    parser.add_argument(
        "--year", type=int, required=True, help="Año de la temporada (ej: 2024)"
    )
    parser.add_argument(
        "--gp",
        type=str,
        required=True,
        metavar="GRAND_PRIX",
        help="Nombre del GP (ej: Miami, Monza, Silverstone)",
    )
    parser.add_argument(
        "--session",
        type=str,
        required=True,
        choices=sorted(VALID_SESSION_TYPES),
        help="Tipo de sesión",
    )
    parser.add_argument(
        "--cache",
        type=str,
        default="data/",
        help="Carpeta de caché de fastf1 (default: data/)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logger.info(
        "Conectando a la DB: %s",
        settings.DATABASE_URL.split("@")[-1],  # no loguear la password
    )

    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as db:
        try:
            result = ingest_session(
                db=db,
                year=args.year,
                grand_prix=args.gp,
                session_type=args.session,
                cache_path=args.cache,
            )
        except Exception as e:
            logger.error("Error durante la ingesta: %s", e)
            sys.exit(1)

    print("\n✓ Ingesta completada:")
    print(f"  Sesión:   {result['session']}")
    print(f"  ID en DB: {result['session_id']}")
    print(f"  Pilotos:  {result['drivers_count']}")
    print(f"  Vueltas:  {result['laps_count']}")
    print(f"  Acción:   {result['action']}")


if __name__ == "__main__":
    main()
