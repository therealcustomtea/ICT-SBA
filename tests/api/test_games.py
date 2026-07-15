from __future__ import annotations

import mastermind_api.services as services
import pytest
from mastermind_api.auth import get_current_user
from mastermind_api.models import GameAttempt, GameSession, LeaderboardEntry, UserAchievement
from sqlalchemy import func, select

from .conftest import APIContext, principal


def pass_and_play_payload() -> dict[str, object]:
    return {
        "mode": "pass_and_play",
        "config": {
            "colours": ["R", "B", "G", "Y", "W"],
            "codeLength": 4,
            "maxAttempts": 3,
            "duplicatesAllowed": True,
            "codeMaker": "human",
            "visibility": "private",
            "ranked": False,
        },
        "secret": ["R", "B", "G", "Y"],
        "idempotencyKey": "create-game-0001",
    }


async def test_authentication_rejection(api: APIContext) -> None:
    api.app.dependency_overrides.pop(get_current_user)
    response = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "normal"})
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_REQUIRED"


async def test_create_secret_omission_attempt_idempotency_and_terminal(api: APIContext) -> None:
    created = await api.client.post("/v1/games", json=pass_and_play_payload())
    assert created.status_code == 201, created.text
    game = created.json()
    assert game["status"] == "active"
    assert game["secret"] is None
    assert game["attemptsUsed"] == 0

    invalid = await api.client.post(
        f"/v1/games/{game['id']}/attempts",
        json={"guess": ["R", "Z", "G", "Y"], "idempotencyKey": "invalid-0000"},
    )
    assert invalid.status_code == 422
    refreshed = await api.client.get(f"/v1/games/{game['id']}")
    assert refreshed.json()["attemptsUsed"] == 0

    won = await api.client.post(
        f"/v1/games/{game['id']}/attempts",
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "attempt-win-000001"},
    )
    assert won.status_code == 200, won.text
    result = won.json()
    assert result["status"] == "won"
    assert result["secret"] == ["R", "B", "G", "Y"]
    assert result["score"] > 0

    retry = await api.client.post(
        f"/v1/games/{game['id']}/attempts",
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "attempt-win-000001"},
    )
    assert retry.status_code == 200
    assert retry.json()["attemptsUsed"] == 1
    reused = await api.client.post(
        f"/v1/games/{game['id']}/attempts",
        json={"guess": ["W", "W", "W", "W"], "idempotencyKey": "attempt-win-000001"},
    )
    assert reused.status_code == 409
    assert reused.json()["code"] == "IDEMPOTENCY_KEY_REUSED"
    after_terminal = await api.client.post(
        f"/v1/games/{game['id']}/attempts",
        json={"guess": ["W", "W", "W", "W"], "idempotencyKey": "attempt-after-0001"},
    )
    assert after_terminal.status_code == 409

    async with api.sessions() as session:
        assert await session.scalar(select(func.count(GameAttempt.id))) == 1
        stored = await session.scalar(
            select(GameSession).where(GameSession.public_id == game["id"])
        )
        assert stored is not None
        assert stored.creation_request_fingerprint is not None
        assert len(stored.creation_request_fingerprint) == 64
        assert stored.encrypted_secret != b'["R","B","G","Y"]'
        assert stored.invalid_submission_count == 1
        assert await session.scalar(select(func.count(UserAchievement.id))) == 0


async def test_creation_idempotency_custom_unranked_and_bola(api: APIContext) -> None:
    first = await api.client.post("/v1/games", json=pass_and_play_payload())
    second = await api.client.post("/v1/games", json=pass_and_play_payload())
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["ranked"] is False
    changed_payload = pass_and_play_payload() | {"secret": ["W", "W", "W", "W"]}
    conflict = await api.client.post("/v1/games", json=changed_payload)
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "IDEMPOTENCY_KEY_REUSED"

    owner = api.current["principal"]
    api.current["principal"] = principal()
    denied = await api.client.get(f"/v1/games/{first.json()['id']}")
    assert denied.status_code == 404
    api.current["principal"] = owner

    async with api.sessions() as session:
        assert await session.scalar(select(func.count(GameSession.id))) == 1
        assert await session.scalar(select(func.count(LeaderboardEntry.id))) == 0


async def test_invalid_configuration_has_stable_error(api: APIContext) -> None:
    response = await api.client.post(
        "/v1/games",
        json={
            "mode": "solo",
            "config": {
                "colours": ["R", "B", "G", "Y", "W"],
                "codeLength": 6,
                "maxAttempts": 10,
                "duplicatesAllowed": False,
            },
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] in {"INSUFFICIENT_UNIQUE_COLOURS", "VALIDATION_ERROR"}


async def test_anonymous_official_win_does_not_award_or_publish(
    api: APIContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))
    api.current["principal"] = principal(anonymous=True)
    created = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    won = await api.client.post(
        f"/v1/games/{created.json()['id']}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "anonymous-win-0001"},
    )
    assert won.status_code == 200
    assert won.json()["status"] == "won"
    async with api.sessions() as session:
        assert await session.scalar(select(func.count(UserAchievement.id))) == 0
        assert await session.scalar(select(func.count(LeaderboardEntry.id))) == 0


async def test_unranked_win_does_not_suppress_first_eligible_break(
    api: APIContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    practice = await api.client.post("/v1/games", json=pass_and_play_payload())
    await api.client.post(
        f"/v1/games/{practice.json()['id']}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "practice-win-0001"},
    )
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))
    official = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    won = await api.client.post(
        f"/v1/games/{official.json()['id']}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "official-win-0001"},
    )
    assert won.status_code == 200 and won.json()["status"] == "won"
    async with api.sessions() as session:
        achievements = set(
            await session.scalars(
                select(UserAchievement.achievement_key).where(
                    UserAchievement.user_id == api.current["principal"].user_id
                )
            )
        )
        assert "first_break" in achievements
