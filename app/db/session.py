# Este módulo configura la conexión a la base de datos y provee
# la "sesión" que se usa para hacer queries.
#
# Concepto clave — Sesión de SQLAlchemy:
#   Una sesión es como una "transacción de trabajo". Acumulás operaciones
#   (INSERT, UPDATE, DELETE) y las confirmás todas juntas con .commit().
#   Si algo falla, hacés .rollback() y no queda nada a medias.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# El engine es la conexión real a la base de datos.
# "pool_pre_ping=True" verifica que la conexión siga viva antes de usarla.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# SessionLocal es una "fábrica" de sesiones. Cada request HTTP crea una sesión nueva.
# autocommit=False → los cambios no se guardan hasta que llamemos .commit()
# autoflush=False  → los cambios no se envían a la DB hasta el commit
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependencia de FastAPI. Crea una sesión de DB por cada request
    y la cierra automáticamente al terminar (incluso si hay un error).

    Se usa así en los endpoints:
        def mi_endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
