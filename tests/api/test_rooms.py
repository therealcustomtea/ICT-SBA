# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `asyncio` so the module can use that dependency.
import asyncio

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import GameSession, MultiplayerEvent, MultiplayerMember

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext, principal


# Defines the `test_room_starts_only_after_both_members_are_ready` callable and its typed interface.
async def test_room_starts_only_after_both_members_are_ready(api: APIContext) -> None:
    # Computes and stores `host` for subsequent operations.
    host = api.current["principal"]
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post("/v1/rooms", json={"difficulty": "easy"})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `room` for subsequent operations.
    room = created.json()
    # Computes and stores `room_id` for subsequent operations.
    room_id = uuid.UUID(room["id"])

    # Computes and stores `host_ready` for subsequent operations.
    host_ready = await api.client.post(f"/v1/rooms/{room_id}/ready")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert host_ready.status_code == 200, host_ready.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert host_ready.json()["status"] == "waiting"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert host_ready.json()["members"][0]["readyAt"] is not None

    # Computes and stores `guest` for subsequent operations.
    guest = principal()
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = guest
    # Computes and stores `joined` for subsequent operations.
    joined = await api.client.post(f"/v1/rooms/{room['roomCode']}/join")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert joined.status_code == 200, joined.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert joined.json()["status"] == "waiting"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all(member["gameId"] is None for member in joined.json()["members"])

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `game_count` for subsequent operations.
        game_count = await session.count(GameSession, {'room_id': room_id})
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game_count == 0

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.app.state.broker.subscribe(str(room_id)) as events:
        # Computes and stores `started` for subsequent operations.
        started = await api.client.post(f"/v1/rooms/{room_id}/ready")
        # Computes and stores `readiness_event` for subsequent operations.
        readiness_event = await asyncio.wait_for(anext(events), timeout=1)
        # Computes and stores `start_event` for subsequent operations.
        start_event = await asyncio.wait_for(anext(events), timeout=1)

    # Asserts this invariant so an unexpected test state fails immediately.
    assert started.status_code == 200, started.text
    # Computes and stores `payload` for subsequent operations.
    payload = started.json()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert payload["status"] == "active"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(payload["members"]) == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all(member["ready"] for member in payload["members"])
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sum(member["gameId"] is not None for member in payload["members"]) == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert next(member for member in payload["members"] if member["gameId"])["userId"] == str(
        # Executes this statement as the next step in the surrounding logic.
        guest.user_id
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert readiness_event["type"] == "member_ready"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert readiness_event["payload"]["userId"] == str(guest.user_id)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert start_event["type"] == "room_started"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert start_event["sequence"] == readiness_event["sequence"] + 1

    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `games` for subsequent operations.
        games = await session.find_many(
            # Supplies this required nested value.
            GameSession, {'room_id': room_id}, sort=[('owner_id', 1)]
        # Closes the multiline declaration, call, or collection opened above.
        )
        # Computes and stores `members` for subsequent operations.
        members = await session.find_many(MultiplayerMember, {'room_id': room_id})
        # Computes and stores `event_types` for subsequent operations.
        event_types = [
            # Supplies this required nested value.
            event.event_type
            # Iterates over these values so each item receives the same processing.
            for event in await session.find_many(
                # Supplies this required nested value.
                MultiplayerEvent, {'room_id': room_id}, sort=[('sequence', 1)]
            # Closes the multiline declaration, call, or collection opened above.
            )
        # Closes the multiline declaration, call, or collection opened above.
        ]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(games) == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert games[0].started_at == games[1].started_at
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all(member.ready and member.ready_at is not None for member in members)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert event_types == ["member_ready", "member_ready", "room_started"]

    # Computes and stores `repeated` for subsequent operations.
    repeated = await api.client.post(f"/v1/rooms/{room_id}/ready")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert repeated.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert repeated.json()["eventSequence"] == payload["eventSequence"]

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = principal()
    # Computes and stores `full` for subsequent operations.
    full = await api.client.post(f"/v1/rooms/{room['roomCode']}/join")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert full.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert full.json()["code"] == "ROOM_FULL"

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = host


# Defines the `test_invalid_room_code_is_generic_not_found` callable and its typed interface.
async def test_invalid_room_code_is_generic_not_found(api: APIContext) -> None:
    # Computes and stores `response` for subsequent operations.
    response = await api.client.post("/v1/rooms/not-a-real-private-room/join")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 404
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.json()["code"] == "ROOM_NOT_FOUND"
