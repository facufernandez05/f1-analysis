# env.py — le dice a Alembic cómo conectarse a la DB y qué modelos mirar.
#
# Concepto clave — Migraciones:
#   Una migración es un script que describe un cambio en el esquema de la DB
#   (crear tabla, agregar columna, etc.). Alembic genera estos scripts automáticamente
#   comparando los modelos SQLAlchemy con el estado actual de la DB.
#
#   Comandos más usados:
#     alembic revision --autogenerate -m "descripcion"  → genera el script
#     alembic upgrade head                               → aplica todas las migraciones
#     alembic downgrade -1                              → revierte la última migración

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Importamos Base y todos los modelos para que Alembic los detecte.
# Si no importás un modelo acá, Alembic no lo va a incluir en el autogenerate.
from app.db.base import Base
from app.db.models import driver, lap, session  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata le dice a Alembic cuál es el "estado deseado" del esquema.
target_metadata = Base.metadata

# Sobreescribir la URL con la variable de entorno si existe.
# Así el mismo env.py funciona en dev (docker) y en CI (sin docker).
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Corre migraciones sin conexión real (genera SQL puro). Útil para revisar."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Corre migraciones con conexión real a la DB."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
