# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `ssl` so the module can use that dependency.
import ssl

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import AsyncIterator

# Imports selected names from `urllib.parse` for use in this module.
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import MetaData

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import (
    # Supplies this item to the surrounding call or collection.
    AsyncEngine,
    # Supplies this item to the surrounding call or collection.
    AsyncSession,
    # Supplies this item to the surrounding call or collection.
    async_sessionmaker,
    # Supplies this item to the surrounding call or collection.
    create_async_engine,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `sqlalchemy.orm` for use in this module.
from sqlalchemy.orm import DeclarativeBase

# Imports selected names from `.config` for use in this module.
from .config import Settings, get_settings, postgres_verify_full_root_certificate

# Computes and stores `NAMING_CONVENTION` for subsequent operations.
NAMING_CONVENTION = {
    # Associates the `ix` key with its value.
    "ix": "ix_%(column_0_label)s",
    # Associates the `uq` key with its value.
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    # Associates the `ck` key with its value.
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    # Associates the `fk` key with its value.
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    # Associates the `pk` key with its value.
    "pk": "pk_%(table_name)s",
    # Closes the multiline call, declaration, or collection started above.
}


# Defines the `Base` class and its related behavior.
class Base(DeclarativeBase):
    # Computes and stores `metadata` for subsequent operations.
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# Defines the `prepare_asyncpg_connection` callable and its typed interface.
def prepare_asyncpg_connection(database_url: str) -> tuple[str, dict[str, object]]:
    # Documents the purpose or contract of this module, class, or function.
    """Translate verify-full URL options into asyncpg's SSLContext input.

    SQLAlchemy expands URL query parameters into ``asyncpg.connect`` keyword
    arguments, but asyncpg accepts ``sslrootcert`` only while parsing a complete
    DSN. Building the context here preserves SQLAlchemy pooling while ensuring
    hostname and certificate verification use the configured CA source.
    """

    # Computes and stores `parsed` for subsequent operations.
    parsed = urlsplit(database_url)
    # Computes and stores `query_items` for subsequent operations.
    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    # Checks this condition before executing the nested branch.
    if [value for name, value in query_items if name == "ssl"] != ["verify-full"]:
        # Returns this result to the caller and ends the current function.
        return database_url, {}
    # Computes and stores `root_certificate` for subsequent operations.
    root_certificate = postgres_verify_full_root_certificate(database_url)
    # Computes and stores `context` for subsequent operations.
    context = ssl.create_default_context(
        # Executes this statement as the next step in the surrounding logic.
        cafile=None if root_certificate == "system" else root_certificate
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `context.check_hostname` for subsequent operations.
    context.check_hostname = True
    # Computes and stores `context.verify_mode` for subsequent operations.
    context.verify_mode = ssl.CERT_REQUIRED
    # Computes and stores `connection_query` for subsequent operations.
    connection_query = urlencode(
        # Executes this statement as the next step in the surrounding logic.
        [(name, value) for name, value in query_items if name not in {"ssl", "sslrootcert"}]
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `connection_url` for subsequent operations.
    connection_url = urlunsplit(parsed._replace(query=connection_query))
    # Returns this result to the caller and ends the current function.
    return connection_url, {"ssl": context}


# Defines the `build_engine` callable and its typed interface.
def build_engine(settings: Settings | None = None) -> AsyncEngine:
    # Computes and stores `config` for subsequent operations.
    config = settings or get_settings()
    # Computes and stores `options` for subsequent operations.
    options: dict[str, object] = {"pool_pre_ping": True}
    # Computes and stores `database_url` for subsequent operations.
    database_url = config.database_url
    # Checks this condition before executing the nested branch.
    if config.database_url.startswith("sqlite"):
        # Computes and stores `options` for subsequent operations.
        options = {}
    # Handles the remaining case not matched by earlier branches.
    else:
        # Executes this statement as the next step in the surrounding logic.
        database_url, connect_args = prepare_asyncpg_connection(config.database_url)
        # Checks this condition before executing the nested branch.
        if connect_args:
            # Executes this statement as the next step in the surrounding logic.
            options["connect_args"] = connect_args
    # Returns this result to the caller and ends the current function.
    return create_async_engine(database_url, **options)


# Computes and stores `engine` for subsequent operations.
engine = build_engine()
# Computes and stores `SessionFactory` for subsequent operations.
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


# Defines the `get_session` callable and its typed interface.
async def get_session() -> AsyncIterator[AsyncSession]:
    # Acquires this asynchronous managed resource for the nested operation.
    async with SessionFactory() as session:
        # Yields this value to the generator consumer without ending iteration.
        yield session
