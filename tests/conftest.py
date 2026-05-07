# conftest.py — configuración compartida para todos los tests.
#
# Concepto clave — Fixtures de pytest:
#   Un fixture es una función que prepara datos/recursos antes de cada test
#   y los limpia después. Con "yield" la parte antes del yield es el "setup"
#   y la parte después es el "teardown".
#
# Concepto clave — Override de dependencias en FastAPI:
#   Durante los tests no queremos usar la DB de producción.
#   FastAPI permite reemplazar cualquier dependencia (como get_db) con otra.
#   Acá la reemplazamos con una sesión de SQLite en memoria: rápida, sin Docker.

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# StaticPool es la clave: fuerza a SQLAlchemy a reusar SIEMPRE la misma conexión.
# Sin esto, SQLite en memoria crea una DB nueva por cada conexión → las tablas
# creadas en el fixture no son visibles cuando llega la request del test.
SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Crea todas las tablas, provee la sesión, y las borra al terminar."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
async def client(db):
    """
    Cliente HTTP de test con la DB de test inyectada.
    Reemplaza get_db con la sesión de SQLite para que los endpoints
    usen la DB de test y no intenten conectarse a Postgres.
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
