# DeclarativeBase es la clase base de la que heredan todos los modelos.
# SQLAlchemy la usa para saber qué tablas existen y cómo mapearlas a clases Python.
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
