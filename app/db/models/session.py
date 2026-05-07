# Modelo de una sesión de F1 (Qualy, Carrera, Practice, etc.)
#
# Concepto clave — ORM (Object-Relational Mapping):
#   En lugar de escribir SQL crudo ("SELECT * FROM sessions"),
#   definís una clase Python y SQLAlchemy genera el SQL por vos.
#   Cada instancia de la clase = una fila en la tabla.

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.lap import Lap


class F1Session(Base):
    # __tablename__ define el nombre real de la tabla en PostgreSQL
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    grand_prix: Mapped[str] = mapped_column(String(100), nullable=False)

    # Tipo de sesión: Q=Qualifying, R=Race, FP1/FP2/FP3=Practice, S=Sprint
    session_type: Mapped[str] = mapped_column(String(10), nullable=False)

    session_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relación con Lap: "una sesión tiene muchas vueltas"
    # back_populates conecta los dos lados de la relación
    laps: Mapped[list["Lap"]] = relationship("Lap", back_populates="session")

    # Restricción: no puede haber dos filas con el mismo año + GP + tipo de sesión
    __table_args__ = (
        UniqueConstraint("year", "grand_prix", "session_type", name="uq_session"),
    )

    def __repr__(self) -> str:
        return f"<F1Session {self.year} {self.grand_prix} {self.session_type}>"
