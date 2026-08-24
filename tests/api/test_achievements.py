# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `mastermind_api.services as services` so the module can use that dependency.
import mastermind_api.services as services

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import UserAchievement

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext


# Defines the `test_comeback_is_awarded_on_the_final_available_attempt` callable and its typed
# interface.
async def test_comeback_is_awarded_on_the_final_available_attempt(
    # Declares the typed `api` data field.
    api: APIContext,
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/games",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `mode` key with its value.
            "mode": "solo",
            # Associates the `config` key with its value.
            "config": {
                # Associates the `colours` key with its value.
                "colours": list("RBGYW"),
                # Associates the `codeLength` key with its value.
                "codeLength": 4,
                # Associates the `maxAttempts` key with its value.
                "maxAttempts": 2,
                # Associates the `duplicatesAllowed` key with its value.
                "duplicatesAllowed": True,
                # Closes the multiline call, declaration, or collection started above.
            },
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `first` for subsequent operations.
    first = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{created.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGW"), "idempotencyKey": "comeback-attempt-01"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.json()["status"] == "active"
    # Computes and stores `final` for subsequent operations.
    final = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{created.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "comeback-attempt-02"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert final.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert final.json()["status"] == "won"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert final.json()["attemptsRemaining"] == 0

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `achievement` for subsequent operations.
        achievement = await session.find_one(
            # Supplies this required nested value.
            UserAchievement,
            # Supplies this required nested value.
            {
                # Supplies this literal value to the surrounding declaration or call.
                "user_id": api.current["principal"].user_id,
                # Supplies this literal value to the surrounding declaration or call.
                "achievement_key": "comeback",
                # Closes the multiline declaration, call, or collection opened above.
            },
            # Closes the multiline declaration, call, or collection opened above.
        )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert achievement is not None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert achievement.game_id is not None
