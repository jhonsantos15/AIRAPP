from __future__ import with_statement
import os
from alembic import context
from logging.config import fileConfig
from flask import current_app

# Alembic Config
config = context.config

# Solo intenta cargar logging desde alembic.ini si el archivo existe
if config.config_file_name and os.path.exists(config.config_file_name):
    fileConfig(config.config_file_name)

# Metadata del modelo desde Flask-Migrate
target_metadata = current_app.extensions["migrate"].db.metadata


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline."""
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online."""
    connectable = current_app.extensions["migrate"].db.engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
