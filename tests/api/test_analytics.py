# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import ProductEvent

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import func, select

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext


# Defines the `game_started_event` callable and its typed interface.
def game_started_event(event_id: uuid.UUID) -> dict[str, object]:
    # Returns this result to the caller and ends the current function.
    return {
        # Associates the `clientEventId` key with its value.
        "clientEventId": str(event_id),
        # Associates the `eventName` key with its value.
        "eventName": "game_started",
        # Associates the `consent` key with its value.
        "consent": True,
        # Associates the `consentVersion` key with its value.
        "consentVersion": "privacy-v1",
        # Associates the `locale` key with its value.
        "locale": "en",
        # Associates the `mode` key with its value.
        "mode": "solo",
        # Associates the `difficulty` key with its value.
        "difficulty": "normal",
        # Closes the multiline call, declaration, or collection started above.
    }


# Defines the `test_analytics_is_disabled_by_default` callable and its typed interface.
async def test_analytics_is_disabled_by_default(api: APIContext) -> None:
    # Computes and stores `response` for subsequent operations.
    response = await api.client.post("/v1/analytics/events", json=game_started_event(uuid.uuid4()))
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 503
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.json()["code"] == "FEATURE_DISABLED"


# Defines the `test_analytics_requires_explicit_consent_and_closed_properties` callable and its
# typed interface.
async def test_analytics_requires_explicit_consent_and_closed_properties(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `api.settings.feature_analytics` for subsequent operations.
    api.settings.feature_analytics = True
    # Computes and stores `no_consent` for subsequent operations.
    no_consent = game_started_event(uuid.uuid4()) | {"consent": False}
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.post("/v1/analytics/events", json=no_consent)).status_code == 422
    # Computes and stores `unsafe` for subsequent operations.
    unsafe = game_started_event(uuid.uuid4()) | {"title": "private challenge title"}
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.post("/v1/analytics/events", json=unsafe)).status_code == 422
    # Computes and stores `wrong_shape` for subsequent operations.
    wrong_shape = game_started_event(uuid.uuid4()) | {"attemptsUsed": 1}
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.post("/v1/analytics/events", json=wrong_shape)).status_code == 422


# Defines the `test_analytics_insert_is_at_most_once_without_runtime_read_access` callable and its
# typed interface.
async def test_analytics_insert_is_at_most_once_without_runtime_read_access(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `api.settings.feature_analytics` for subsequent operations.
    api.settings.feature_analytics = True
    # Computes and stores `event_id` for subsequent operations.
    event_id = uuid.uuid4()
    # Computes and stores `payload` for subsequent operations.
    payload = game_started_event(event_id)
    # Computes and stores `first` for subsequent operations.
    first = await api.client.post("/v1/analytics/events", json=payload)
    # Computes and stores `retry` for subsequent operations.
    retry = await api.client.post("/v1/analytics/events", json=payload)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.status_code == retry.status_code == 202
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.json() == {"received": True}
    # Computes and stores `changed` for subsequent operations.
    changed = await api.client.post("/v1/analytics/events", json=payload | {"difficulty": "hard"})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert changed.status_code == 202
    # Asserts this invariant so an unexpected test state fails immediately.
    assert changed.json() == {"received": True}
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.scalar(select(func.count(ProductEvent.id))) == 1
        # Computes and stores `event` for subsequent operations.
        event = await session.scalar(select(ProductEvent))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert event is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert event.event_name == "game_started"
        # Asserts this invariant so an unexpected test state fails immediately.
        assert event.difficulty == "normal"
        # Asserts this invariant so an unexpected test state fails immediately.
        assert event.anonymous is False
        # Asserts this invariant so an unexpected test state fails immediately.
        assert not hasattr(event, "user_id")
