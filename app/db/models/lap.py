# Modelo de una vuelta
#
# Concepto clave — Foreign Keys:
#   Una FK es un campo que apunta al ID de otra tabla.
#   Aquí, cada vuelta sabe a qué sesión y a qué piloto pertenece.
#   Esto evita duplicar datos y permite hacer JOINs eficientes.

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.driver import Driver
    from app.db.models.session import F1Session


class Lap(Base):
    __tablename__ = "laps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ForeignKey: este campo referencia al id de la tabla "sessions"
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sessions.id"), nullable=False, index=True
    )
    driver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("drivers.id"), nullable=False, index=True
    )

    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Tiempos en milisegundos (más preciso que segundos)
    lap_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector1_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector2_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector3_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_personal_best: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relaciones: "esta vuelta pertenece a una sesión y a un piloto"
    session: Mapped["F1Session"] = relationship("F1Session", back_populates="laps")
    driver: Mapped["Driver"] = relationship("Driver", back_populates="laps")

    def __repr__(self) -> str:
        return (
            f"<Lap session={self.session_id} "
            f"driver={self.driver_id} lap={self.lap_number}>"
        )
