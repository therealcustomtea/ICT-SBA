from __future__ import annotations

import ssl
from collections.abc import AsyncIterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import Settings, get_settings, postgres_verify_full_root_certificate

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def prepare_asyncpg_connection(database_url: str) -> tuple[str, dict[str, object]]:
    """Translate verify-full URL options into asyncpg's SSLContext input.

    SQLAlchemy expands URL query parameters into ``asyncpg.connect`` keyword
    arguments, but asyncpg accepts ``sslrootcert`` only while parsing a complete
    DSN. Building the context here preserves SQLAlchemy pooling while ensuring
    hostname and certificate verification use the configured CA source.
    """

    parsed = urlsplit(database_url)
    query_items = parse_qsl(parsed.query, keep_blank_values=True)
    if [value for name, value in query_items if name == "ssl"] != ["verify-full"]:
        return database_url, {}
    root_certificate = postgres_verify_full_root_certificate(database_url)
    context = ssl.create_default_context(
        cafile=None if root_certificate == "system" else root_certificate
    )
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    connection_query = urlencode(
        [(name, value) for name, value in query_items if name not in {"ssl", "sslrootcert"}]
    )
    connection_url = urlunsplit(parsed._replace(query=connection_query))
    return connection_url, {"ssl": context}


def build_engine(settings: Settings | None = None) -> AsyncEngine:
    config = settings or get_settings()
    options: dict[str, object] = {"pool_pre_ping": True}
    database_url = config.database_url
    if config.database_url.startswith("sqlite"):
        options = {}
    else:
        database_url, connect_args = prepare_asyncpg_connection(config.database_url)
        if connect_args:
            options["connect_args"] = connect_args
    return create_async_engine(database_url, **options)


engine = build_engine()
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
