# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `base64` because this module uses that dependency.
import base64

# Imports `json` because this module uses that dependency.
import json

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports the required names from `collections.abc` for this module.
from collections.abc import AsyncIterator

# Imports the required names from `dataclasses` for this module.
from dataclasses import dataclass

# Imports the required names from `datetime` for this module.
from datetime import UTC, datetime

# Imports `httpx` because this module uses that dependency.
import httpx

# Imports `pytest_asyncio` because this module uses that dependency.
import pytest_asyncio

# Imports the required names from `fastapi` for this module.
from fastapi import FastAPI

# Imports the required names from `mastermind_api.auth` for this module.
from mastermind_api.auth import AuthPrincipal, get_current_user

# Imports the required names from `mastermind_api.config` for this module.
from mastermind_api.config import Settings, get_settings

# Imports the required names from `mastermind_api.database` for this module.
from mastermind_api.database import MongoSession, MongoSessionFactory, get_session

# Imports the required names from `mastermind_api.main` for this module.
from mastermind_api.main import create_app

# Imports the required names from `pymongo` for this module.
from pymongo import AsyncMongoClient


# Defines this callable to implement the operation described by its name.
def principal(user_id: uuid.UUID | None = None, *, anonymous: bool = False) -> AuthPrincipal:
    # Returns the computed result and ends the current callable.
    return AuthPrincipal(
        # Stores `user_id` because later steps depend on this value.
        user_id=user_id or uuid.uuid4(),
        # Stores `is_anonymous` because later steps depend on this value.
        is_anonymous=anonymous,
        # Stores `session_id` because later steps depend on this value.
        session_id=str(uuid.uuid4()),
        # Stores `issued_at` because later steps depend on this value.
        issued_at=datetime.now(UTC),
        # Stores `authenticated_at` because later steps depend on this value.
        authenticated_at=datetime.now(UTC),
        # Stores `assurance_level` because later steps depend on this value.
        assurance_level="aal1",
        # Closes the multiline declaration, call, or collection opened above.
    )


# Applies this decorator to configure the declaration immediately below.
@dataclass(slots=True)
# Groups the state and behavior owned by `APIContext`.
class APIContext:
    # Declares this typed field so the surrounding contract is explicit.
    app: FastAPI
    # Declares this typed field so the surrounding contract is explicit.
    client: httpx.AsyncClient
    # Declares this typed field so the surrounding contract is explicit.
    sessions: MongoSessionFactory
    # Declares this typed field so the surrounding contract is explicit.
    current: dict[str, AuthPrincipal]
    # Declares this typed field so the surrounding contract is explicit.
    settings: Settings


# Applies this decorator to configure the declaration immediately below.
@pytest_asyncio.fixture
# Defines this callable to implement the operation described by its name.
async def api() -> AsyncIterator[APIContext]:
    # Stores `base_settings` because later steps depend on this value.
    base_settings = get_settings()
    # Stores `database_name` because later steps depend on this value.
    database_name = f"cbtest_{uuid.uuid4().hex[:24]}"
    # Stores `key` because later steps depend on this value.
    key = base64.b64encode(b"e" * 32).decode()
    # Stores `settings` because later steps depend on this value.
    settings = Settings(
        # Stores `environment` because later steps depend on this value.
        environment="test",
        # Stores `mongodb_url` because later steps depend on this value.
        mongodb_url=base_settings.mongodb_url,
        # Stores `mongodb_database` because later steps depend on this value.
        mongodb_database=database_name,
        # Stores `redis_url` because later steps depend on this value.
        redis_url=None,
        # Stores `auth_signing_key` because later steps depend on this value.
        auth_signing_key="test-auth-signing-key-material-32-bytes",
        # Stores `secret_encryption_keys` because later steps depend on this value.
        secret_encryption_keys=json.dumps({"v1": key}),
        # Stores `secret_active_key_version` because later steps depend on this value.
        secret_active_key_version="v1",
        # Stores `daily_hmac_key` because later steps depend on this value.
        daily_hmac_key="d" * 32,
        # Stores `public_identifier_hmac_key` because later steps depend on this value.
        public_identifier_hmac_key="i" * 32,
        # Stores `rate_limit_per_minute` because later steps depend on this value.
        rate_limit_per_minute=1000,
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Stores `sessions` because later steps depend on this value.
    sessions = MongoSessionFactory()

    # Defines this callable to implement the operation described by its name.
    async def session_override() -> AsyncIterator[MongoSession]:
        # Scopes this resource so acquisition and cleanup remain paired.
        async with sessions() as session:
            # Supplies this required nested value.
            yield session

    # Stores `current` because later steps depend on this value.
    current = {"principal": principal()}

    # Defines this callable to implement the operation described by its name.
    def auth_override() -> AuthPrincipal:
        # Returns the computed result and ends the current callable.
        return current["principal"]

    # Stores `app` because later steps depend on this value.
    app = create_app(settings)
    # Supplies this required nested value.
    app.dependency_overrides[get_session] = session_override
    # Supplies this required nested value.
    app.dependency_overrides[get_current_user] = auth_override
    # Scopes this resource so acquisition and cleanup remain paired.
    async with app.router.lifespan_context(app):
        # Stores `transport` because later steps depend on this value.
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        # Scopes this resource so acquisition and cleanup remain paired.
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Supplies this required nested value.
            yield APIContext(app, client, sessions, current, settings)

    # Stores `cleanup_client` because later steps depend on this value.
    cleanup_client: AsyncMongoClient[dict[str, object]] = AsyncMongoClient(
        # Supplies this required nested value.
        settings.mongodb_url,
        uuidRepresentation="standard",
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Starts an operation whose expected failures are handled below.
    try:
        # Performs this required operation before the surrounding flow continues.
        await cleanup_client.drop_database(database_name)
    # Ensures this cleanup runs whether the protected operation succeeds or fails.
    finally:
        # Performs this required operation before the surrounding flow continues.
        await cleanup_client.close()
