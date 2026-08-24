# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `mastermind_api.services as services` so the module can use that dependency.
import mastermind_api.services as services

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.auth` for use in this module.
from mastermind_api.auth import get_current_user

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import GameSession, LeaderboardEntry, UserAchievement

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext, principal


# Defines the `pass_and_play_payload` callable and its typed interface.
def pass_and_play_payload() -> dict[str, object]:
    # Returns this result to the caller and ends the current function.
    return {
        # Associates the `mode` key with its value.
        "mode": "pass_and_play",
        # Associates the `config` key with its value.
        "config": {
            # Associates the `colours` key with its value.
            "colours": ["R", "B", "G", "Y", "W"],
            # Associates the `codeLength` key with its value.
            "codeLength": 4,
            # Associates the `maxAttempts` key with its value.
            "maxAttempts": 3,
            # Associates the `duplicatesAllowed` key with its value.
            "duplicatesAllowed": True,
            # Associates the `codeMaker` key with its value.
            "codeMaker": "human",
            # Associates the `visibility` key with its value.
            "visibility": "private",
            # Associates the `ranked` key with its value.
            "ranked": False,
            # Closes the multiline call, declaration, or collection started above.
        },
        # Associates the `secret` key with its value.
        "secret": ["R", "B", "G", "Y"],
        # Associates the `idempotencyKey` key with its value.
        "idempotencyKey": "create-game-0001",
        # Closes the multiline call, declaration, or collection started above.
    }


# Defines the `test_authentication_rejection` callable and its typed interface.
async def test_authentication_rejection(api: APIContext) -> None:
    # Calls `api.app.dependency_overrides.pop` with the supplied values.
    api.app.dependency_overrides.pop(get_current_user)
    # Computes and stores `response` for subsequent operations.
    response = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "normal"})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 401
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


# Defines the `test_create_secret_omission_attempt_idempotency_and_terminal` callable and its typed
# interface.
async def test_create_secret_omission_attempt_idempotency_and_terminal(api: APIContext) -> None:
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post("/v1/games", json=pass_and_play_payload())
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `game` for subsequent operations.
    game = created.json()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert game["status"] == "active"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert game["secret"] is None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert game["attemptsUsed"] == 0

    # Computes and stores `invalid` for subsequent operations.
    invalid = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{game['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": ["R", "Z", "G", "Y"], "idempotencyKey": "invalid-0000"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert invalid.status_code == 422
    # Computes and stores `refreshed` for subsequent operations.
    refreshed = await api.client.get(f"/v1/games/{game['id']}")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert refreshed.json()["attemptsUsed"] == 0

    # Computes and stores `won` for subsequent operations.
    won = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{game['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "attempt-win-000001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert won.status_code == 200, won.text
    # Computes and stores `result` for subsequent operations.
    result = won.json()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert result["status"] == "won"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert result["secret"] == ["R", "B", "G", "Y"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert result["score"] > 0

    # Computes and stores `retry` for subsequent operations.
    retry = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{game['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "attempt-win-000001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retry.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retry.json()["attemptsUsed"] == 1
    # Computes and stores `reused` for subsequent operations.
    reused = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{game['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": ["W", "W", "W", "W"], "idempotencyKey": "attempt-win-000001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert reused.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert reused.json()["code"] == "IDEMPOTENCY_KEY_REUSED"
    # Computes and stores `after_terminal` for subsequent operations.
    after_terminal = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{game['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": ["W", "W", "W", "W"], "idempotencyKey": "attempt-after-0001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert after_terminal.status_code == 409

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert len((await session.find_one(GameSession, {'public_id': game['id']})).attempts) == 1
        # Computes and stores `stored` for subsequent operations.
        stored = await session.find_one(GameSession, {'public_id': game['id']})
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored.creation_request_fingerprint is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert len(stored.creation_request_fingerprint) == 64
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored.encrypted_secret != b'["R","B","G","Y"]'
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored.invalid_submission_count == 1
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.count(UserAchievement) == 0


# Defines the `test_creation_idempotency_custom_unranked_and_bola` callable and its typed interface.
async def test_creation_idempotency_custom_unranked_and_bola(api: APIContext) -> None:
    # Computes and stores `first` for subsequent operations.
    first = await api.client.post("/v1/games", json=pass_and_play_payload())
    # Computes and stores `second` for subsequent operations.
    second = await api.client.post("/v1/games", json=pass_and_play_payload())
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.status_code == second.status_code == 201
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.json()["id"] == second.json()["id"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.json()["ranked"] is False
    # Computes and stores `changed_payload` for subsequent operations.
    changed_payload = pass_and_play_payload() | {"secret": ["W", "W", "W", "W"]}
    # Computes and stores `conflict` for subsequent operations.
    conflict = await api.client.post("/v1/games", json=changed_payload)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert conflict.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert conflict.json()["code"] == "IDEMPOTENCY_KEY_REUSED"

    # Computes and stores `owner` for subsequent operations.
    owner = api.current["principal"]
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = principal()
    # Computes and stores `denied` for subsequent operations.
    denied = await api.client.get(f"/v1/games/{first.json()['id']}")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert denied.status_code == 404
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = owner

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.count(GameSession) == 1
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.count(LeaderboardEntry) == 0


# Defines the `test_invalid_configuration_has_stable_error` callable and its typed interface.
async def test_invalid_configuration_has_stable_error(api: APIContext) -> None:
    # Computes and stores `response` for subsequent operations.
    response = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/games",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `mode` key with its value.
            "mode": "solo",
            # Associates the `config` key with its value.
            "config": {
                # Associates the `colours` key with its value.
                "colours": ["R", "B", "G", "Y", "W"],
                # Associates the `codeLength` key with its value.
                "codeLength": 6,
                # Associates the `maxAttempts` key with its value.
                "maxAttempts": 10,
                # Associates the `duplicatesAllowed` key with its value.
                "duplicatesAllowed": False,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 422
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.json()["code"] in {"INSUFFICIENT_UNIQUE_COLOURS", "VALIDATION_ERROR"}


# Defines the `test_anonymous_official_win_does_not_award_or_publish` callable and its typed
# interface.
async def test_anonymous_official_win_does_not_award_or_publish(
    # Declares the typed `api` data field.
    api: APIContext,
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = principal(anonymous=True)
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    # Computes and stores `won` for subsequent operations.
    won = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{created.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "anonymous-win-0001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert won.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert won.json()["status"] == "won"
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.count(UserAchievement) == 0
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.count(LeaderboardEntry) == 0


# Defines the `test_unranked_win_does_not_suppress_first_eligible_break` callable and its typed
# interface.
async def test_unranked_win_does_not_suppress_first_eligible_break(
    # Declares the typed `api` data field.
    api: APIContext,
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `practice` for subsequent operations.
    practice = await api.client.post("/v1/games", json=pass_and_play_payload())
    # Waits for this asynchronous operation to complete.
    await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{practice.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "practice-win-0001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))
    # Computes and stores `official` for subsequent operations.
    official = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    # Computes and stores `won` for subsequent operations.
    won = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{official.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "official-win-0001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert won.status_code == 200 and won.json()["status"] == "won"
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `achievements` for subsequent operations.
        achievements = {
            # Supplies this required nested value.
            item.achievement_key
            # Iterates over these values so each item receives the same processing.
            for item in await session.find_many(
                # Supplies this required nested value.
                UserAchievement, {'user_id': api.current['principal'].user_id}
            # Closes the multiline declaration, call, or collection opened above.
            )
        # Closes the multiline declaration, call, or collection opened above.
        }
        # Asserts this invariant so an unexpected test state fails immediately.
        assert "first_break" in achievements
