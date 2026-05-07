# Migración inicial: crea las tablas sessions, drivers y laps.
#
# Concepto clave — estructura de una migración:
#   upgrade()   → se ejecuta con "alembic upgrade head"   (aplica cambios)
#   downgrade() → se ejecuta con "alembic downgrade -1"   (revierte cambios)
#
#   Alembic guarda en una tabla interna "alembic_version" cuál fue la última
#   migración aplicada, así sabe desde dónde continuar la próxima vez.

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers
revision: str = "8b2ca896748d"
down_revision: Union[str, None] = None  # None = es la primera migración
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Tabla: drivers ---
    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("team", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_drivers_id", "drivers", ["id"])
    op.create_index("ix_drivers_code", "drivers", ["code"], unique=True)

    # --- Tabla: sessions ---
    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("grand_prix", sa.String(length=100), nullable=False),
        sa.Column("session_type", sa.String(length=10), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("year", "grand_prix", "session_type", name="uq_session"),
    )
    op.create_index("ix_sessions_id", "sessions", ["id"])

    # --- Tabla: laps ---
    op.create_table(
        "laps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("driver_id", sa.Integer(), nullable=False),
        sa.Column("lap_number", sa.Integer(), nullable=False),
        sa.Column("lap_time_ms", sa.Float(), nullable=True),
        sa.Column("sector1_ms", sa.Float(), nullable=True),
        sa.Column("sector2_ms", sa.Float(), nullable=True),
        sa.Column("sector3_ms", sa.Float(), nullable=True),
        sa.Column("is_personal_best", sa.Boolean(), nullable=True),
        # FK hacia sessions y drivers
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_laps_id", "laps", ["id"])
    op.create_index("ix_laps_session_id", "laps", ["session_id"])
    op.create_index("ix_laps_driver_id", "laps", ["driver_id"])


def downgrade() -> None:
    op.drop_index("ix_laps_driver_id", table_name="laps")
    op.drop_index("ix_laps_session_id", table_name="laps")
    op.drop_index("ix_laps_id", table_name="laps")
    op.drop_table("laps")

    op.drop_index("ix_sessions_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_index("ix_drivers_code", table_name="drivers")
    op.drop_index("ix_drivers_id", table_name="drivers")
    op.drop_table("drivers")
