from __future__ import annotations

from datetime import date

from mastermind_api.dependencies import get_cipher
from mastermind_api.models import DailyChallenge, GameSession
from mastermind_api.services import get_or_create_daily
from mastermind_core import derive_daily_secret, get_preset
from sqlalchemy import select

from .conftest import APIContext


async def test_daily_consistency_official_uniqueness_and_practice_replay(api: APIContext) -> None:
    definition = await api.client.get("/v1/daily")
    assert definition.status_code == 200, definition.text
    first = await api.client.post("/v1/daily/start")
    second = await api.client.post("/v1/daily/start")
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["mode"] == "daily"

    secret = derive_daily_secret(
        date.fromisoformat(definition.json()["date"]), get_preset("normal"), b"d" * 32
    )
    completed = await api.client.post(
        f"/v1/games/{first.json()['id']}/attempts",
        json={"guess": list(secret), "idempotencyKey": "daily-attempt-0001"},
    )
    assert completed.status_code == 200
    official_again = await api.client.post("/v1/daily/start", json={"practice": False})
    assert official_again.json()["id"] == first.json()["id"]
    practice = await api.client.post("/v1/daily/start", json={"practice": True})
    assert practice.status_code == 200, practice.text
    assert practice.json()["id"] != first.json()["id"]
    assert practice.json()["mode"] == "practice"
    assert practice.json()["ranked"] is False

    async with api.sessions() as session:
        rows = (
            await session.scalars(
                select(GameSession).where(GameSession.owner_id == api.current["principal"].user_id)
            )
        ).all()
        assert sum(row.daily_challenge_id is not None for row in rows) == 1


async def test_daily_rollover_has_distinct_definition_without_persisted_secret(
    api: APIContext,
) -> None:
    cipher = get_cipher(api.settings)
    async with api.sessions() as session:
        first = await get_or_create_daily(session, api.settings, cipher, date(2026, 7, 15))
        second = await get_or_create_daily(session, api.settings, cipher, date(2026, 7, 16))
        assert first.public_id != second.public_id
        assert "daily_hmac_v1" in first.public_id
        columns = set(DailyChallenge.__table__.columns.keys())
        assert "encrypted_secret" not in columns
        assert "secret_nonce" not in columns
