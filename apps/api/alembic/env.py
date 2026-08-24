# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `os` so the module can use that dependency.
import os

# Imports selected names from `logging.config` for use in this module.
from logging.config import fileConfig

# Imports selected names from `alembic` for use in this module.
from alembic import context

# Imports selected names from `mastermind_api` for use in this module.
from mastermind_api import models as _models  # noqa: F401

# Imports selected names from `mastermind_api.config` for use in this module.
from mastermind_api.config import get_settings, validate_deployed_postgres_url

# Imports selected names from `mastermind_api.database` for use in this module.
from mastermind_api.database import Base, prepare_asyncpg_connection

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import Connection, pool

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import async_engine_from_config

# Computes and stores `config` for subsequent operations.
config = context.config
# Checks this condition before executing the nested branch.
if config.config_file_name is not None:
    # Calls `fileConfig` with the supplied values.
    fileConfig(config.config_file_name)

# Computes and stores `settings` for subsequent operations.
settings = get_settings()
# Computes and stores `migration_url` for subsequent operations.
migration_url = os.getenv("DATABASE_MIGRATOR_URL") or settings.database_url
# Checks this condition before executing the nested branch.
if settings.environment in {"staging", "production"}:
    # Calls `validate_deployed_postgres_url` with the supplied values.
    validate_deployed_postgres_url(migration_url)
# Executes this statement as the next step in the surrounding logic.
migration_engine_url, migration_connect_args = prepare_asyncpg_connection(migration_url)
# Calls `config.set_main_option` with the supplied values.
config.set_main_option("sqlalchemy.url", migration_engine_url.replace("%", "%%"))
# Computes and stores `target_metadata` for subsequent operations.
target_metadata = Base.metadata


# Defines the `run_migrations_offline` callable and its typed interface.
def run_migrations_offline() -> None:
    # Calls `context.configure` with the supplied values.
    context.configure(
        # Provides the `url` parameter or keyword argument.
        url=config.get_main_option("sqlalchemy.url"),
        # Provides the `target_metadata` parameter or keyword argument.
        target_metadata=target_metadata,
        # Provides the `literal_binds` parameter or keyword argument.
        literal_binds=True,
        # Provides the `dialect_opts` parameter or keyword argument.
        dialect_opts={"paramstyle": "named"},
        # Provides the `compare_type` parameter or keyword argument.
        compare_type=True,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this managed resource and guarantees cleanup afterward.
    with context.begin_transaction():
        # Calls `context.run_migrations` with the supplied values.
        context.run_migrations()


# Defines the `do_run_migrations` callable and its typed interface.
def do_run_migrations(connection: Connection) -> None:
    # Calls `context.configure` with the supplied values.
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    # Acquires this managed resource and guarantees cleanup afterward.
    with context.begin_transaction():
        # Calls `context.run_migrations` with the supplied values.
        context.run_migrations()


# Defines the `run_async_migrations` callable and its typed interface.
async def run_async_migrations() -> None:
    # Computes and stores `connectable` for subsequent operations.
    connectable = async_engine_from_config(
        # Calls `config.get_section` with the supplied values.
        config.get_section(config.config_ini_section, {}),
        # Provides the `prefix` parameter or keyword argument.
        prefix="sqlalchemy.",
        # Provides the `poolclass` parameter or keyword argument.
        poolclass=pool.NullPool,
        # Provides the `connect_args` parameter or keyword argument.
        connect_args=migration_connect_args,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this asynchronous managed resource for the nested operation.
    async with connectable.connect() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(do_run_migrations)
    # Waits for this asynchronous operation to complete.
    await connectable.dispose()


# Checks this condition before executing the nested branch.
if context.is_offline_mode():
    # Calls `run_migrations_offline` with the supplied values.
    run_migrations_offline()
# Handles the remaining case not matched by earlier branches.
else:
    # Calls `asyncio.run` with the supplied values.
    asyncio.run(run_async_migrations())
