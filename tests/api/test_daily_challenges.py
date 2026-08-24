# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports the required names from `dataclasses` for this module.
from dataclasses import fields

# Imports selected names from `datetime` for use in this module.
from datetime import date

# Imports selected names from `mastermind_api.dependencies` for use in this module.
from mastermind_api.dependencies import get_cipher

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import DailyChallenge, GameSession

# Imports selected names from `mastermind_api.services` for use in this module.
from mastermind_api.services import get_or_create_daily

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import derive_daily_secret, get_preset

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext


# Defines the `test_daily_consistency_official_uniqueness_and_practice_replay` callable and its
# typed interface.
async def test_daily_consistency_official_uniqueness_and_practice_replay(api: APIContext) -> None:
    # Computes and stores `definition` for subsequent operations.
    definition = await api.client.get("/v1/daily")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert definition.status_code == 200, definition.text
    # Computes and stores `first` for subsequent operations.
    first = await api.client.post("/v1/daily/start")
    # Computes and stores `second` for subsequent operations.
    second = await api.client.post("/v1/daily/start")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.status_code == second.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.json()["id"] == second.json()["id"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.json()["mode"] == "daily"

    # Computes and stores `secret` for subsequent operations.
    secret = derive_daily_secret(
        # Calls `date.fromisoformat` with the supplied values.
        date.fromisoformat(definition.json()["date"]),
        # Calls `get_preset` with these supplied values.
        get_preset("normal"),
        # Supplies this item to the surrounding call or collection.
        b"d" * 32,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `completed` for subsequent operations.
    completed = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{first.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list(secret), "idempotencyKey": "daily-attempt-0001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert completed.status_code == 200
    # Computes and stores `official_again` for subsequent operations.
    official_again = await api.client.post("/v1/daily/start", json={"practice": False})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert official_again.json()["id"] == first.json()["id"]
    # Computes and stores `practice` for subsequent operations.
    practice = await api.client.post("/v1/daily/start", json={"practice": True})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert practice.status_code == 200, practice.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert practice.json()["id"] != first.json()["id"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert practice.json()["mode"] == "practice"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert practice.json()["ranked"] is False

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `rows` for subsequent operations.
        rows = await session.find_many(
            # Supplies this required nested value.
            GameSession, {'owner_id': api.current['principal'].user_id}
        # Closes the multiline declaration, call, or collection opened above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert sum(row.daily_challenge_id is not None for row in rows) == 1


# Defines the `test_daily_rollover_has_distinct_definition_without_persisted_secret` callable and
# its typed interface.
async def test_daily_rollover_has_distinct_definition_without_persisted_secret(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `cipher` for subsequent operations.
    cipher = get_cipher(api.settings)
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `first` for subsequent operations.
        first = await get_or_create_daily(session, api.settings, cipher, date(2026, 7, 15))
        # Computes and stores `second` for subsequent operations.
        second = await get_or_create_daily(session, api.settings, cipher, date(2026, 7, 16))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert first.public_id != second.public_id
        # Asserts this invariant so an unexpected test state fails immediately.
        assert "daily_hmac_v1" in first.public_id
        # Computes and stores `columns` for subsequent operations.
        columns = {item.name for item in fields(DailyChallenge)}
        # Asserts this invariant so an unexpected test state fails immediately.
        assert "encrypted_secret" not in columns
        # Asserts this invariant so an unexpected test state fails immediately.
        assert "secret_nonce" not in columns
