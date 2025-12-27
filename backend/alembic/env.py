from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.engine.url import make_url

# P1-001: Correct import path for settings
from app.core.database import SQLModel # Use absolute path
# Import all models to register with metadata
from app.models import (
    sql_models, game_models, robot_models, growth_models, bonus_models, reconciliation,
    engine_models, payment_models, poker_models, poker_mtt_models, poker_table_models,
    rg_models, payment_analytics_models, reconciliation_run, sql_models_extended, vip_models
)
from app.repositories import ledger_repo
from config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=False, # P1: Disable type comparison to avoid SQLite TEXT/VARCHAR drift noise
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _get_sync_url(async_url: str) -> str:
    """Normalize async URLs (aiosqlite/asyncpg) to sync drivers for Alembic.

    Alembic uses synchronous DB drivers under the hood. This helper ensures that
    we can point migrations at the same database as the async application layer
    without requiring async drivers in the migration context.
    """

    url = make_url(async_url)
    drivername = url.drivername

    if drivername.endswith("+aiosqlite"):
        url = url.set(drivername="sqlite")
    elif drivername.endswith("+asyncpg"):
        url = url.set(drivername="postgresql")

    return str(url)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using a synchronous engine."""

    sync_url = _get_sync_url(settings.database_url)

    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
