from __future__ import annotations

import base64
import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest_asyncio
from fastapi import FastAPI
from mastermind_api.auth import AuthPrincipal, get_current_user
from mastermind_api.config import Settings
from mastermind_api.database import Base, get_session
from mastermind_api.main import create_app
from mastermind_api.models import Achievement, FeatureFlag
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def principal(user_id: uuid.UUID | None = None, *, anonymous: bool = False) -> AuthPrincipal:
    return AuthPrincipal(
        user_id=user_id or uuid.uuid4(),
        is_anonymous=anonymous,
        session_id=str(uuid.uuid4()),
        issued_at=datetime.now(UTC),
        authenticated_at=datetime.now(UTC),
        assurance_level="aal1",
    )


@dataclass(slots=True)
class APIContext:
    app: FastAPI
    client: httpx.AsyncClient
    sessions: async_sessionmaker[AsyncSession]
    current: dict[str, AuthPrincipal]
    settings: Settings


@pytest_asyncio.fixture
async def api(tmp_path: Path) -> AsyncIterator[APIContext]:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'api.sqlite'}"
    key = base64.b64encode(b"e" * 32).decode()
    settings = Settings(
        environment="test",
        database_url=database_url,
        redis_url=None,
        supabase_url="https://example.supabase.co",
        secret_encryption_keys=json.dumps({"v1": key}),
        secret_active_key_version="v1",
        daily_hmac_key="d" * 32,
        public_identifier_hmac_key="i" * 32,
        rate_limit_per_minute=1000,
    )
    test_engine = create_async_engine(database_url)
    sessions = async_sessionmaker(test_engine, expire_on_commit=False)
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with sessions() as seed_session:
        seed_session.add_all(
            [
                Achievement(
                    key=key,
                    name=key.replace("_", " ").title(),
                    description="Test achievement definition.",
                )
                for key in (
                    "first_break",
                    "one_shot",
                    "no_waste",
                    "daily_debut",
                    "logic_week",
                    "hard_mode",
                    "expert_breaker",
                    "challenger",
                    "duelist",
                    "comeback",
                )
            ]
        )
        seed_session.add(FeatureFlag(key="daily", enabled=True))
        await seed_session.commit()

    async def session_override() -> AsyncIterator[AsyncSession]:
        async with sessions() as session:
            yield session

    current = {"principal": principal()}

    def auth_override() -> AuthPrincipal:
        return current["principal"]

    app = create_app(settings)
    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[get_current_user] = auth_override
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield APIContext(app, client, sessions, current, settings)
    await test_engine.dispose()
