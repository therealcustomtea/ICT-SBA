from __future__ import annotations

import hashlib
import json
import uuid
from datetime import timedelta

import mastermind_api.services as services
import pytest
from mastermind_api.models import FriendChallenge, GameSession, MultiplayerEvent, MultiplayerRoom
from mastermind_api.services import utcnow
from sqlalchemy import select

from .conftest import APIContext, principal


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def setex(self, key: str, _seconds: int, value: str) -> None:
        self.values[key] = value

    async def getdel(self, key: str) -> str | None:
        return self.values.pop(key, None)

    async def ping(self) -> bool:
        return True


async def test_friend_invite_hash_revoke_expiry_and_replay(api: APIContext) -> None:
    creator = api.current["principal"]
    created = await api.client.post(
        "/v1/challenges",
        json={
            "difficulty": "normal",
            "secret": ["R", "B", "G", "Y"],
            "title": "A careful challenge",
            "showCreatorName": False,
            "idempotencyKey": "friend-create-0001",
        },
    )
    assert created.status_code == 201, created.text
    challenge = created.json()
    share_code = challenge["shareCode"]
    retried = await api.client.post(
        "/v1/challenges",
        json={
            "difficulty": "normal",
            "secret": ["R", "B", "G", "Y"],
            "title": "A careful challenge",
            "showCreatorName": False,
            "idempotencyKey": "friend-create-0001",
        },
    )
    assert retried.json()["id"] == challenge["id"]
    assert retried.json()["shareCode"] == share_code
    changed_retry = await api.client.post(
        "/v1/challenges",
        json={
            "difficulty": "normal",
            "secret": ["R", "B", "G", "Y"],
            "title": "A different challenge",
            "showCreatorName": False,
            "idempotencyKey": "friend-create-0001",
        },
    )
    assert changed_retry.status_code == 409
    assert changed_retry.json()["code"] == "IDEMPOTENCY_KEY_REUSED"
    async with api.sessions() as session:
        stored = await session.scalar(select(FriendChallenge))
        assert stored is not None
        assert stored.creation_request_fingerprint is not None
        assert stored.share_code_hash != share_code
        challenge_id = stored.id

    api.current["principal"] = principal()
    visible = await api.client.get(f"/v1/challenges/{share_code}")
    assert visible.status_code == 200
    assert visible.json()["creatorName"] is None
    started = await api.client.post(f"/v1/challenges/{share_code}/start")
    won = await api.client.post(
        f"/v1/games/{started.json()['id']}/attempts",
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "friend-attempt-001"},
    )
    assert won.json()["status"] == "won"
    practice = await api.client.post(f"/v1/challenges/{share_code}/start", json={"practice": True})
    assert practice.json()["mode"] == "practice"
    assert practice.json()["id"] != started.json()["id"]

    api.current["principal"] = creator
    results = await api.client.get(f"/v1/challenges/{challenge_id}/results")
    assert results.status_code == 200, results.text
    assert results.json()["completedCount"] == 1
    assert results.json()["winRate"] == 100.0
    assert results.json()["items"][0]["playerLabel"].startswith("Breaker ")
    assert "userId" not in results.json()["items"][0]
    revoked = await api.client.delete(f"/v1/challenges/{challenge_id}")
    assert revoked.status_code == 204
    revoked = await api.client.get(f"/v1/challenges/{share_code}")
    assert revoked.status_code == 404
    assert revoked.json()["code"] == "CHALLENGE_NOT_FOUND"

    another = await api.client.post(
        "/v1/challenges",
        json={"difficulty": "easy", "title": "Expires"},
    )
    async with api.sessions() as session:
        first_challenge = await session.get(FriendChallenge, challenge_id)
        assert first_challenge is not None
        expiring = await session.scalar(
            select(FriendChallenge).where(
                FriendChallenge.share_code_hash != first_challenge.share_code_hash
            )
        )
        assert expiring is not None
        expiring.expires_at = utcnow() - timedelta(seconds=1)
        await session.commit()
    assert (
        await api.client.get(f"/v1/challenges/{another.json()['shareCode']}")
    ).status_code == 404


async def test_friend_results_follow_score_tie_breaks_and_keep_players_private(
    api: APIContext,
) -> None:
    creator = api.current["principal"]
    created = await api.client.post(
        "/v1/challenges",
        json={
            "difficulty": "normal",
            "secret": ["R", "B", "G", "Y"],
            "title": "Ordered results",
        },
    )
    assert created.status_code == 201, created.text
    challenge = created.json()

    game_ids: list[str] = []
    for index in range(6):
        api.current["principal"] = principal()
        started = await api.client.post(f"/v1/challenges/{challenge['shareCode']}/start")
        assert started.status_code == 200, started.text
        game_id = started.json()["id"]
        completed = await api.client.post(
            f"/v1/games/{game_id}/attempts",
            json={
                "guess": ["R", "B", "G", "Y"],
                "idempotencyKey": f"ordered-result-{index:02d}",
            },
        )
        assert completed.status_code == 200 and completed.json()["status"] == "won"
        game_ids.append(game_id)

    now = utcnow()
    async with api.sessions() as session:
        games = list(
            await session.scalars(select(GameSession).where(GameSession.public_id.in_(game_ids)))
        )
        by_public_id = {game.public_id: game for game in games}
        # Higher score, fewer attempts, shorter time, earlier completion, then public ID.
        specifications = {
            game_ids[0]: (1400, 6, 120, now),
            game_ids[1]: (1300, 1, 120, now),
            game_ids[2]: (1300, 2, 30, now),
            game_ids[3]: (1300, 2, 60, now - timedelta(seconds=1)),
            game_ids[4]: (1300, 2, 60, now),
            game_ids[5]: (1300, 2, 60, now),
        }
        for public_id, values in specifications.items():
            game = by_public_id[public_id]
            game.final_score, game.attempts_used, game.elapsed_seconds, game.completed_at = values
        await session.commit()

    stable_order = sorted(game_ids[4:])
    expected = [game_ids[0], game_ids[1], game_ids[2], game_ids[3], *stable_order]
    unauthorized = await api.client.get(f"/v1/challenges/{challenge['id']}/results")
    assert unauthorized.status_code == 404
    assert unauthorized.json()["code"] == "CHALLENGE_NOT_FOUND"

    api.current["principal"] = creator
    response = await api.client.get(
        f"/v1/challenges/{challenge['id']}/results?page=1&page_size=100"
    )
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert [item["playerLabel"] for item in items] == [
        f"Breaker {public_id[:6].upper()}" for public_id in expected
    ]
    assert [item["rank"] for item in items] == [1, 2, 3, 4, 5, 6]
    assert items[0]["elapsedSeconds"] == 120
    assert all("userId" not in item and "displayName" not in item for item in items)

    second_page = await api.client.get(
        f"/v1/challenges/{challenge['id']}/results?page=2&page_size=2"
    )
    assert second_page.status_code == 200
    assert [item["rank"] for item in second_page.json()["items"]] == [3, 4]


async def test_room_code_hash_membership_and_one_use_ws_ticket(api: APIContext) -> None:
    host = api.current["principal"]
    created = await api.client.post(
        "/v1/rooms",
        json={"difficulty": "normal", "idempotencyKey": "room-create-00001"},
    )
    assert created.status_code == 201, created.text
    room = created.json()
    room_code = room["roomCode"]
    retried = await api.client.post(
        "/v1/rooms",
        json={"difficulty": "normal", "idempotencyKey": "room-create-00001"},
    )
    assert retried.json()["id"] == room["id"]
    assert retried.json()["roomCode"] == room_code
    changed_retry = await api.client.post(
        "/v1/rooms",
        json={"difficulty": "hard", "idempotencyKey": "room-create-00001"},
    )
    assert changed_retry.status_code == 409
    assert changed_retry.json()["code"] == "IDEMPOTENCY_KEY_REUSED"
    assert room["status"] == "waiting"
    assert room["members"][0]["gameId"] is None
    assert room["members"][0]["ready"] is False
    host_ready = await api.client.post(f"/v1/rooms/{room['id']}/ready")
    assert host_ready.status_code == 200, host_ready.text
    assert host_ready.json()["status"] == "waiting"
    assert host_ready.json()["members"][0]["ready"] is True
    async with api.sessions() as session:
        stored = await session.get(MultiplayerRoom, uuid.UUID(room["id"]))
        assert stored is not None
        assert stored.creation_request_fingerprint is not None
        assert stored.room_code_hash != room_code

    guest = principal()
    api.current["principal"] = guest
    joined = await api.client.post(f"/v1/rooms/{room_code}/join")
    assert joined.status_code == 200, joined.text
    assert joined.json()["roomCode"] is None
    assert len(joined.json()["members"]) == 2
    assert joined.json()["status"] == "waiting"
    assert all(member["gameId"] is None for member in joined.json()["members"])

    started = await api.client.post(f"/v1/rooms/{room['id']}/ready")
    assert started.status_code == 200, started.text
    assert started.json()["status"] == "active"
    assert all(member["ready"] for member in started.json()["members"])
    assert sum(member["gameId"] is not None for member in started.json()["members"]) == 1
    retried_ready = await api.client.post(f"/v1/rooms/{room['id']}/ready")
    assert retried_ready.status_code == 200
    assert retried_ready.json()["eventSequence"] == started.json()["eventSequence"]

    api.current["principal"] = host
    host_room = (await api.client.get(f"/v1/rooms/{room['id']}")).json()
    host_game_id = next(
        member["gameId"] for member in host_room["members"] if member["userId"] == str(host.user_id)
    )
    blocked = await api.client.post(
        f"/v1/games/{host_game_id}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "duel-http-attempt-1"},
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "REALTIME_ENDPOINT_REQUIRED"

    api.current["principal"] = principal()
    assert (await api.client.get(f"/v1/rooms/{room['id']}")).status_code == 404

    api.current["principal"] = guest
    fake_redis = FakeRedis()
    api.app.state.redis = fake_redis
    api.app.state.redis_ready = True
    ticket_response = await api.client.post(f"/v1/rooms/{room['id']}/ws-ticket")
    assert ticket_response.status_code == 200, ticket_response.text
    ticket = ticket_response.json()["ticket"]
    key = f"mastermind:ws-ticket:{hashlib.sha256(ticket.encode()).hexdigest()}"
    stored_ticket = await fake_redis.getdel(key)
    assert stored_ticket is not None
    assert json.loads(stored_ticket)["userId"] == str(guest.user_id)
    assert await fake_redis.getdel(key) is None

    guest_game_id = next(
        member["gameId"]
        for member in started.json()["members"]
        if member["userId"] == str(guest.user_id)
    )
    async with api.app.state.broker.subscribe(room["id"]) as events:
        abandoned = await api.client.post(f"/v1/games/{guest_game_id}/abandon")
        assert abandoned.status_code == 200, abandoned.text
        published = await anext(events)
    assert published["version"] == 1
    assert published["type"] == "room_completed"
    assert published["payload"] == {
        "winnerId": str(host.user_id),
        "isTie": False,
        "reason": "forfeit",
    }
    async with api.sessions() as session:
        stored_event = await session.scalar(
            select(MultiplayerEvent).where(
                MultiplayerEvent.room_id == uuid.UUID(room["id"]),
                MultiplayerEvent.event_type == "room_completed",
            )
        )
        assert stored_event is not None

    api.current["principal"] = host


async def test_active_friend_challenge_allowance_is_bounded(
    api: APIContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "MAX_ACTIVE_CHALLENGES_PER_USER", 2)
    for title in ("First", "Second"):
        response = await api.client.post(
            "/v1/challenges", json={"difficulty": "easy", "title": title}
        )
        assert response.status_code == 201
    blocked = await api.client.post("/v1/challenges", json={"difficulty": "easy", "title": "Third"})
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "CHALLENGE_LIMIT_REACHED"


async def test_creator_can_return_to_private_challenge_management(api: APIContext) -> None:
    owner = api.current["principal"]
    created = await api.client.post(
        "/v1/challenges",
        json={"difficulty": "normal", "title": "A private rematch"},
    )
    assert created.status_code == 201, created.text

    listing = await api.client.get("/v1/challenges/mine")
    assert listing.status_code == 200, listing.text
    assert listing.json()["total"] == 1
    item = listing.json()["items"][0]
    assert item["id"] == created.json()["id"]
    assert item["title"] == "A private rematch"
    assert item["completedCount"] == 0
    assert "shareCode" not in item

    api.current["principal"] = principal()
    other_listing = await api.client.get("/v1/challenges/mine")
    assert other_listing.status_code == 200
    assert other_listing.json()["items"] == []
    api.current["principal"] = owner


async def test_guest_friend_challenge_allowance_is_three(api: APIContext) -> None:
    api.current["principal"] = principal(anonymous=True)
    for index in range(3):
        response = await api.client.post(
            "/v1/challenges",
            json={"difficulty": "easy", "title": f"Guest challenge {index}"},
        )
        assert response.status_code == 201
    blocked = await api.client.post(
        "/v1/challenges", json={"difficulty": "easy", "title": "Guest challenge 4"}
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "CHALLENGE_LIMIT_REACHED"
