# Modelo de un piloto

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.lap import Lap


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Código de 3 letras que usa la F1: VER, HAM, COL, etc.
    code: Mapped[str] = mapped_column(
        String(3), unique=True, nullable=False, index=True
    )

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    team: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relación: "un piloto tiene muchas vueltas"
    laps: Mapped[list["Lap"]] = relationship("Lap", back_populates="driver")

    def __repr__(self) -> str:
        return f"<Driver {self.code} - {self.full_name}>"
