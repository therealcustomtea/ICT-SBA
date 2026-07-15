from __future__ import annotations

import mastermind_api.services as services
import pytest
from mastermind_api.models import UserAchievement
from sqlalchemy import select

from .conftest import APIContext


async def test_comeback_is_awarded_on_the_final_available_attempt(
    api: APIContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))
    created = await api.client.post(
        "/v1/games",
        json={
            "mode": "solo",
            "config": {
                "colours": list("RBGYW"),
                "codeLength": 4,
                "maxAttempts": 2,
                "duplicatesAllowed": True,
            },
        },
    )
    assert created.status_code == 201, created.text
    first = await api.client.post(
        f"/v1/games/{created.json()['id']}/attempts",
        json={"guess": list("RBGW"), "idempotencyKey": "comeback-attempt-01"},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "active"
    final = await api.client.post(
        f"/v1/games/{created.json()['id']}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "comeback-attempt-02"},
    )
    assert final.status_code == 200
    assert final.json()["status"] == "won"
    assert final.json()["attemptsRemaining"] == 0

    async with api.sessions() as session:
        achievement = await session.scalar(
            select(UserAchievement).where(
                UserAchievement.user_id == api.current["principal"].user_id,
                UserAchievement.achievement_key == "comeback",
            )
        )
    assert achievement is not None
    assert achievement.game_id is not None
