from __future__ import annotations

import asyncio
import uuid

from mastermind_api.models import GameSession, MultiplayerEvent, MultiplayerMember
from sqlalchemy import func, select

from .conftest import APIContext, principal


async def test_room_starts_only_after_both_members_are_ready(api: APIContext) -> None:
    host = api.current["principal"]
    created = await api.client.post("/v1/rooms", json={"difficulty": "easy"})
    assert created.status_code == 201, created.text
    room = created.json()
    room_id = uuid.UUID(room["id"])

    host_ready = await api.client.post(f"/v1/rooms/{room_id}/ready")
    assert host_ready.status_code == 200, host_ready.text
    assert host_ready.json()["status"] == "waiting"
    assert host_ready.json()["members"][0]["readyAt"] is not None

    guest = principal()
    api.current["principal"] = guest
    joined = await api.client.post(f"/v1/rooms/{room['roomCode']}/join")
    assert joined.status_code == 200, joined.text
    assert joined.json()["status"] == "waiting"
    assert all(member["gameId"] is None for member in joined.json()["members"])

    async with api.sessions() as session:
        game_count = await session.scalar(
            select(func.count(GameSession.id)).where(GameSession.room_id == room_id)
        )
        assert game_count == 0

    async with api.app.state.broker.subscribe(str(room_id)) as events:
        started = await api.client.post(f"/v1/rooms/{room_id}/ready")
        readiness_event = await asyncio.wait_for(anext(events), timeout=1)
        start_event = await asyncio.wait_for(anext(events), timeout=1)

    assert started.status_code == 200, started.text
    payload = started.json()
    assert payload["status"] == "active"
    assert len(payload["members"]) == 2
    assert all(member["ready"] for member in payload["members"])
    assert sum(member["gameId"] is not None for member in payload["members"]) == 1
    assert next(member for member in payload["members"] if member["gameId"])["userId"] == str(
        guest.user_id
    )
    assert readiness_event["type"] == "member_ready"
    assert readiness_event["payload"]["userId"] == str(guest.user_id)
    assert start_event["type"] == "room_started"
    assert start_event["sequence"] == readiness_event["sequence"] + 1

    async with api.sessions() as session:
        games = (
            await session.scalars(
                select(GameSession)
                .where(GameSession.room_id == room_id)
                .order_by(GameSession.owner_id)
            )
        ).all()
        members = (
            await session.scalars(
                select(MultiplayerMember).where(MultiplayerMember.room_id == room_id)
            )
        ).all()
        event_types = list(
            await session.scalars(
                select(MultiplayerEvent.event_type)
                .where(MultiplayerEvent.room_id == room_id)
                .order_by(MultiplayerEvent.sequence)
            )
        )
    assert len(games) == 2
    assert games[0].started_at == games[1].started_at
    assert all(member.ready and member.ready_at is not None for member in members)
    assert event_types == ["member_ready", "member_ready", "room_started"]

    repeated = await api.client.post(f"/v1/rooms/{room_id}/ready")
    assert repeated.status_code == 200
    assert repeated.json()["eventSequence"] == payload["eventSequence"]

    api.current["principal"] = principal()
    full = await api.client.post(f"/v1/rooms/{room['roomCode']}/join")
    assert full.status_code == 409
    assert full.json()["code"] == "ROOM_FULL"

    api.current["principal"] = host


async def test_invalid_room_code_is_generic_not_found(api: APIContext) -> None:
    response = await api.client.post("/v1/rooms/not-a-real-private-room/join")
    assert response.status_code == 404
    assert response.json()["code"] == "ROOM_NOT_FOUND"
