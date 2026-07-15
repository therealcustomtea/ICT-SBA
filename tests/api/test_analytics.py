from __future__ import annotations

import uuid

from mastermind_api.models import ProductEvent
from sqlalchemy import func, select

from .conftest import APIContext


def game_started_event(event_id: uuid.UUID) -> dict[str, object]:
    return {
        "clientEventId": str(event_id),
        "eventName": "game_started",
        "consent": True,
        "consentVersion": "privacy-v1",
        "locale": "en",
        "mode": "solo",
        "difficulty": "normal",
    }


async def test_analytics_is_disabled_by_default(api: APIContext) -> None:
    response = await api.client.post("/v1/analytics/events", json=game_started_event(uuid.uuid4()))
    assert response.status_code == 503
    assert response.json()["code"] == "FEATURE_DISABLED"


async def test_analytics_requires_explicit_consent_and_closed_properties(
    api: APIContext,
) -> None:
    api.settings.feature_analytics = True
    no_consent = game_started_event(uuid.uuid4()) | {"consent": False}
    assert (await api.client.post("/v1/analytics/events", json=no_consent)).status_code == 422
    unsafe = game_started_event(uuid.uuid4()) | {"title": "private challenge title"}
    assert (await api.client.post("/v1/analytics/events", json=unsafe)).status_code == 422
    wrong_shape = game_started_event(uuid.uuid4()) | {"attemptsUsed": 1}
    assert (await api.client.post("/v1/analytics/events", json=wrong_shape)).status_code == 422


async def test_analytics_insert_is_at_most_once_without_runtime_read_access(
    api: APIContext,
) -> None:
    api.settings.feature_analytics = True
    event_id = uuid.uuid4()
    payload = game_started_event(event_id)
    first = await api.client.post("/v1/analytics/events", json=payload)
    retry = await api.client.post("/v1/analytics/events", json=payload)
    assert first.status_code == retry.status_code == 202
    assert first.json() == {"received": True}
    changed = await api.client.post("/v1/analytics/events", json=payload | {"difficulty": "hard"})
    assert changed.status_code == 202
    assert changed.json() == {"received": True}
    async with api.sessions() as session:
        assert await session.scalar(select(func.count(ProductEvent.id))) == 1
        event = await session.scalar(select(ProductEvent))
        assert event is not None
        assert event.event_name == "game_started"
        assert event.difficulty == "normal"
        assert event.anonymous is False
        assert not hasattr(event, "user_id")
