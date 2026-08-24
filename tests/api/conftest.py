# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `base64` so the module can use that dependency.
import base64

# Imports `json` so the module can use that dependency.
import json

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import AsyncIterator

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import dataclass

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime

# Imports selected names from `pathlib` for use in this module.
from pathlib import Path

# Imports `httpx` so the module can use that dependency.
import httpx

# Imports `pytest_asyncio` so the module can use that dependency.
import pytest_asyncio

# Imports selected names from `fastapi` for use in this module.
from fastapi import FastAPI

# Imports selected names from `mastermind_api.auth` for use in this module.
from mastermind_api.auth import AuthPrincipal, get_current_user

# Imports selected names from `mastermind_api.config` for use in this module.
from mastermind_api.config import Settings

# Imports selected names from `mastermind_api.database` for use in this module.
from mastermind_api.database import Base, get_session

# Imports selected names from `mastermind_api.main` for use in this module.
from mastermind_api.main import create_app

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import Achievement, FeatureFlag

# Imports selected names from `sqlalchemy.ext.asyncio` for use in this module.
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# Defines the `principal` callable and its typed interface.
def principal(user_id: uuid.UUID | None = None, *, anonymous: bool = False) -> AuthPrincipal:
    # Returns this result to the caller and ends the current function.
    return AuthPrincipal(
        # Provides the `user_id` parameter or keyword argument.
        user_id=user_id or uuid.uuid4(),
        # Provides the `is_anonymous` parameter or keyword argument.
        is_anonymous=anonymous,
        # Provides the `session_id` parameter or keyword argument.
        session_id=str(uuid.uuid4()),
        # Provides the `issued_at` parameter or keyword argument.
        issued_at=datetime.now(UTC),
        # Provides the `authenticated_at` parameter or keyword argument.
        authenticated_at=datetime.now(UTC),
        # Provides the `assurance_level` parameter or keyword argument.
        assurance_level="aal1",
        # Closes the multiline call, declaration, or collection started above.
    )


# Applies `@dataclass(slots=True)` to configure the declaration immediately below.
@dataclass(slots=True)
# Defines the `APIContext` class and its related behavior.
class APIContext:
    # Declares the typed `app` data field.
    app: FastAPI
    # Declares the typed `client` data field.
    client: httpx.AsyncClient
    # Declares the typed `sessions` data field.
    sessions: async_sessionmaker[AsyncSession]
    # Declares the typed `current` data field.
    current: dict[str, AuthPrincipal]
    # Declares the typed `settings` data field.
    settings: Settings


# Applies `@pytest_asyncio.fixture` to configure the declaration immediately below.
@pytest_asyncio.fixture
# Defines the `api` callable and its typed interface.
async def api(tmp_path: Path) -> AsyncIterator[APIContext]:
    # Computes and stores `database_url` for subsequent operations.
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'api.sqlite'}"
    # Computes and stores `key` for subsequent operations.
    key = base64.b64encode(b"e" * 32).decode()
    # Computes and stores `settings` for subsequent operations.
    settings = Settings(
        # Provides the `environment` parameter or keyword argument.
        environment="test",
        # Provides the `database_url` parameter or keyword argument.
        database_url=database_url,
        # Provides the `redis_url` parameter or keyword argument.
        redis_url=None,
        # Provides the `supabase_url` parameter or keyword argument.
        supabase_url="https://example.supabase.co",
        # Provides the `secret_encryption_keys` parameter or keyword argument.
        secret_encryption_keys=json.dumps({"v1": key}),
        # Provides the `secret_active_key_version` parameter or keyword argument.
        secret_active_key_version="v1",
        # Provides the `daily_hmac_key` parameter or keyword argument.
        daily_hmac_key="d" * 32,
        # Provides the `public_identifier_hmac_key` parameter or keyword argument.
        public_identifier_hmac_key="i" * 32,
        # Provides the `rate_limit_per_minute` parameter or keyword argument.
        rate_limit_per_minute=1000,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `test_engine` for subsequent operations.
    test_engine = create_async_engine(database_url)
    # Computes and stores `sessions` for subsequent operations.
    sessions = async_sessionmaker(test_engine, expire_on_commit=False)
    # Acquires this asynchronous managed resource for the nested operation.
    async with test_engine.begin() as connection:
        # Waits for this asynchronous operation to complete.
        await connection.run_sync(Base.metadata.create_all)
    # Acquires this asynchronous managed resource for the nested operation.
    async with sessions() as seed_session:
        # Calls `seed_session.add_all` with the supplied values.
        seed_session.add_all(
            # Begins the nested block or multiline expression completed below.
            [
                # Calls `Achievement` with the supplied values.
                Achievement(
                    # Provides the `key` parameter or keyword argument.
                    key=key,
                    # Provides the `name` parameter or keyword argument.
                    name=key.replace("_", " ").title(),
                    # Provides the `description` parameter or keyword argument.
                    description="Test achievement definition.",
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Iterates through the supplied values for the nested operation.
                for key in (
                    # Supplies this item to the surrounding call or collection.
                    "first_break",
                    # Supplies this item to the surrounding call or collection.
                    "one_shot",
                    # Supplies this item to the surrounding call or collection.
                    "no_waste",
                    # Supplies this item to the surrounding call or collection.
                    "daily_debut",
                    # Supplies this item to the surrounding call or collection.
                    "logic_week",
                    # Supplies this item to the surrounding call or collection.
                    "hard_mode",
                    # Supplies this item to the surrounding call or collection.
                    "expert_breaker",
                    # Supplies this item to the surrounding call or collection.
                    "challenger",
                    # Supplies this item to the surrounding call or collection.
                    "duelist",
                    # Supplies this item to the surrounding call or collection.
                    "comeback",
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `seed_session.add` with the supplied values.
        seed_session.add(FeatureFlag(key="daily", enabled=True))
        # Waits for this asynchronous operation to complete.
        await seed_session.commit()

    # Defines the `session_override` callable and its typed interface.
    async def session_override() -> AsyncIterator[AsyncSession]:
        # Acquires this asynchronous managed resource for the nested operation.
        async with sessions() as session:
            # Yields this value to the generator consumer without ending iteration.
            yield session

    # Computes and stores `current` for subsequent operations.
    current = {"principal": principal()}

    # Defines the `auth_override` callable and its typed interface.
    def auth_override() -> AuthPrincipal:
        # Returns this result to the caller and ends the current function.
        return current["principal"]

    # Computes and stores `app` for subsequent operations.
    app = create_app(settings)
    # Executes this statement as the next step in the surrounding logic.
    app.dependency_overrides[get_session] = session_override
    # Executes this statement as the next step in the surrounding logic.
    app.dependency_overrides[get_current_user] = auth_override
    # Acquires this asynchronous managed resource for the nested operation.
    async with app.router.lifespan_context(app):
        # Computes and stores `transport` for subsequent operations.
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        # Acquires this asynchronous managed resource for the nested operation.
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Yields this value to the generator consumer without ending iteration.
            yield APIContext(app, client, sessions, current, settings)
    # Waits for this asynchronous operation to complete.
    await test_engine.dispose()
