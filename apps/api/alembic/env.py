from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from mastermind_api import models as _models  # noqa: F401
from mastermind_api.config import get_settings, validate_deployed_postgres_url
from mastermind_api.database import Base, prepare_asyncpg_connection
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
migration_url = os.getenv("DATABASE_MIGRATOR_URL") or settings.database_url
if settings.environment in {"staging", "production"}:
    validate_deployed_postgres_url(migration_url)
migration_engine_url, migration_connect_args = prepare_asyncpg_connection(migration_url)
config.set_main_option("sqlalchemy.url", migration_engine_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=migration_connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
