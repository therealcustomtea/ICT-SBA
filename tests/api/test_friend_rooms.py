# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `hashlib` so the module can use that dependency.
import hashlib

# Imports `json` so the module can use that dependency.
import json

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports selected names from `datetime` for use in this module.
from datetime import timedelta

# Imports `mastermind_api.services as services` so the module can use that dependency.
import mastermind_api.services as services

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import FriendChallenge, GameSession, MultiplayerEvent, MultiplayerRoom

# Imports selected names from `mastermind_api.services` for use in this module.
from mastermind_api.services import utcnow

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext, principal


# Defines the `FakeRedis` class and its related behavior.
class FakeRedis:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self) -> None:
        # Computes and stores `self.values` for subsequent operations.
        self.values: dict[str, str] = {}

    # Defines the `setex` callable and its typed interface.
    async def setex(self, key: str, _seconds: int, value: str) -> None:
        # Executes this statement as the next step in the surrounding logic.
        self.values[key] = value

    # Defines the `getdel` callable and its typed interface.
    async def getdel(self, key: str) -> str | None:
        # Returns this result to the caller and ends the current function.
        return self.values.pop(key, None)

    # Defines the `ping` callable and its typed interface.
    async def ping(self) -> bool:
        # Returns this result to the caller and ends the current function.
        return True


# Defines the `test_friend_invite_hash_revoke_expiry_and_replay` callable and its typed interface.
async def test_friend_invite_hash_revoke_expiry_and_replay(api: APIContext) -> None:
    # Computes and stores `creator` for subsequent operations.
    creator = api.current["principal"]
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/challenges",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `difficulty` key with its value.
            "difficulty": "normal",
            # Associates the `secret` key with its value.
            "secret": ["R", "B", "G", "Y"],
            # Associates the `title` key with its value.
            "title": "A careful challenge",
            # Associates the `showCreatorName` key with its value.
            "showCreatorName": False,
            # Associates the `idempotencyKey` key with its value.
            "idempotencyKey": "friend-create-0001",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `challenge` for subsequent operations.
    challenge = created.json()
    # Computes and stores `share_code` for subsequent operations.
    share_code = challenge["shareCode"]
    # Computes and stores `retried` for subsequent operations.
    retried = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/challenges",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `difficulty` key with its value.
            "difficulty": "normal",
            # Associates the `secret` key with its value.
            "secret": ["R", "B", "G", "Y"],
            # Associates the `title` key with its value.
            "title": "A careful challenge",
            # Associates the `showCreatorName` key with its value.
            "showCreatorName": False,
            # Associates the `idempotencyKey` key with its value.
            "idempotencyKey": "friend-create-0001",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retried.json()["id"] == challenge["id"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retried.json()["shareCode"] == share_code
    # Computes and stores `changed_retry` for subsequent operations.
    changed_retry = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/challenges",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `difficulty` key with its value.
            "difficulty": "normal",
            # Associates the `secret` key with its value.
            "secret": ["R", "B", "G", "Y"],
            # Associates the `title` key with its value.
            "title": "A different challenge",
            # Associates the `showCreatorName` key with its value.
            "showCreatorName": False,
            # Associates the `idempotencyKey` key with its value.
            "idempotencyKey": "friend-create-0001",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert changed_retry.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert changed_retry.json()["code"] == "IDEMPOTENCY_KEY_REUSED"
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `stored` for subsequent operations.
        stored = await session.find_one(FriendChallenge, {})
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored.creation_request_fingerprint is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored.share_code_hash != share_code
        # Computes and stores `challenge_id` for subsequent operations.
        challenge_id = stored.id

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = principal()
    # Computes and stores `visible` for subsequent operations.
    visible = await api.client.get(f"/v1/challenges/{share_code}")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert visible.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert visible.json()["creatorName"] is None
    # Computes and stores `started` for subsequent operations.
    started = await api.client.post(f"/v1/challenges/{share_code}/start")
    # Computes and stores `won` for subsequent operations.
    won = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{started.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "friend-attempt-001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert won.json()["status"] == "won"
    # Computes and stores `practice` for subsequent operations.
    practice = await api.client.post(f"/v1/challenges/{share_code}/start", json={"practice": True})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert practice.json()["mode"] == "practice"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert practice.json()["id"] != started.json()["id"]

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = creator
    # Computes and stores `results` for subsequent operations.
    results = await api.client.get(f"/v1/challenges/{challenge_id}/results")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert results.status_code == 200, results.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert results.json()["completedCount"] == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert results.json()["winRate"] == 100.0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert results.json()["items"][0]["playerLabel"].startswith("Breaker ")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "userId" not in results.json()["items"][0]
    # Computes and stores `revoked` for subsequent operations.
    revoked = await api.client.delete(f"/v1/challenges/{challenge_id}")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert revoked.status_code == 204
    # Computes and stores `revoked` for subsequent operations.
    revoked = await api.client.get(f"/v1/challenges/{share_code}")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert revoked.status_code == 404
    # Asserts this invariant so an unexpected test state fails immediately.
    assert revoked.json()["code"] == "CHALLENGE_NOT_FOUND"

    # Computes and stores `another` for subsequent operations.
    another = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/challenges",
        # Provides the `json` parameter or keyword argument.
        json={"difficulty": "easy", "title": "Expires"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `first_challenge` for subsequent operations.
        first_challenge = await session.get(FriendChallenge, challenge_id)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert first_challenge is not None
        # Computes and stores `expiring` for subsequent operations.
        expiring = await session.find_one(
            # Supplies this required nested value.
            FriendChallenge,
            # Supplies this required nested value.
            {"share_code_hash": {"$ne": first_challenge.share_code_hash}},
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert expiring is not None
        # Computes and stores `expiring.expires_at` for subsequent operations.
        expiring.expires_at = utcnow() - timedelta(seconds=1)
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (
        # Waits for this asynchronous operation to complete.
        await api.client.get(f"/v1/challenges/{another.json()['shareCode']}")
        # Executes this statement as the next step in the surrounding logic.
    ).status_code == 404


# Defines the `test_friend_results_follow_score_tie_breaks_and_keep_players_private` callable and
# its typed interface.
async def test_friend_results_follow_score_tie_breaks_and_keep_players_private(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `creator` for subsequent operations.
    creator = api.current["principal"]
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/challenges",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `difficulty` key with its value.
            "difficulty": "normal",
            # Associates the `secret` key with its value.
            "secret": ["R", "B", "G", "Y"],
            # Associates the `title` key with its value.
            "title": "Ordered results",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `challenge` for subsequent operations.
    challenge = created.json()

    # Computes and stores `game_ids` for subsequent operations.
    game_ids: list[str] = []
    # Iterates through the supplied values for the nested operation.
    for index in range(6):
        # Executes this statement as the next step in the surrounding logic.
        api.current["principal"] = principal()
        # Computes and stores `started` for subsequent operations.
        started = await api.client.post(f"/v1/challenges/{challenge['shareCode']}/start")
        # Asserts this invariant so an unexpected test state fails immediately.
        assert started.status_code == 200, started.text
        # Computes and stores `game_id` for subsequent operations.
        game_id = started.json()["id"]
        # Computes and stores `completed` for subsequent operations.
        completed = await api.client.post(
            # Supplies this item to the surrounding call or collection.
            f"/v1/games/{game_id}/attempts",
            # Computes and stores `json` for subsequent operations.
            json={
                # Associates the `guess` key with its value.
                "guess": ["R", "B", "G", "Y"],
                # Associates the `idempotencyKey` key with its value.
                "idempotencyKey": f"ordered-result-{index:02d}",
                # Closes the multiline call, declaration, or collection started above.
            },
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert completed.status_code == 200 and completed.json()["status"] == "won"
        # Calls `game_ids.append` with the supplied values.
        game_ids.append(game_id)

    # Computes and stores `now` for subsequent operations.
    now = utcnow()
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `games` for subsequent operations.
        games = await session.find_many(GameSession, {"public_id": {"$in": game_ids}})
        # Computes and stores `by_public_id` for subsequent operations.
        by_public_id = {game.public_id: game for game in games}
        # Higher score, fewer attempts, shorter time, earlier completion, then public ID.
        # Computes and stores `specifications` for subsequent operations.
        specifications = {
            # Supplies this item to the surrounding call or collection.
            game_ids[0]: (1400, 6, 120, now),
            # Supplies this item to the surrounding call or collection.
            game_ids[1]: (1300, 1, 120, now),
            # Supplies this item to the surrounding call or collection.
            game_ids[2]: (1300, 2, 30, now),
            # Supplies this item to the surrounding call or collection.
            game_ids[3]: (1300, 2, 60, now - timedelta(seconds=1)),
            # Supplies this item to the surrounding call or collection.
            game_ids[4]: (1300, 2, 60, now),
            # Supplies this item to the surrounding call or collection.
            game_ids[5]: (1300, 2, 60, now),
            # Closes the multiline call, declaration, or collection started above.
        }
        # Iterates through the supplied values for the nested operation.
        for public_id, values in specifications.items():
            # Computes and stores `game` for subsequent operations.
            game = by_public_id[public_id]
            # Executes this statement as the next step in the surrounding logic.
            game.final_score, game.attempts_used, game.elapsed_seconds, game.completed_at = values
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `stable_order` for subsequent operations.
    stable_order = sorted(game_ids[4:])
    # Computes and stores `expected` for subsequent operations.
    expected = [game_ids[0], game_ids[1], game_ids[2], game_ids[3], *stable_order]
    # Computes and stores `unauthorized` for subsequent operations.
    unauthorized = await api.client.get(f"/v1/challenges/{challenge['id']}/results")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert unauthorized.status_code == 404
    # Asserts this invariant so an unexpected test state fails immediately.
    assert unauthorized.json()["code"] == "CHALLENGE_NOT_FOUND"

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = creator
    # Computes and stores `response` for subsequent operations.
    response = await api.client.get(
        # Executes this statement as the next step in the surrounding logic.
        f"/v1/challenges/{challenge['id']}/results?page=1&page_size=100"
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert response.status_code == 200, response.text
    # Computes and stores `items` for subsequent operations.
    items = response.json()["items"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert [item["playerLabel"] for item in items] == [
        # Executes this statement as the next step in the surrounding logic.
        f"Breaker {public_id[:6].upper()}"
        # Continues the surrounding expression or operation.
        for public_id in expected
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert [item["rank"] for item in items] == [1, 2, 3, 4, 5, 6]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert items[0]["elapsedSeconds"] == 120
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all("userId" not in item and "displayName" not in item for item in items)

    # Computes and stores `second_page` for subsequent operations.
    second_page = await api.client.get(
        # Executes this statement as the next step in the surrounding logic.
        f"/v1/challenges/{challenge['id']}/results?page=2&page_size=2"
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert second_page.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert [item["rank"] for item in second_page.json()["items"]] == [3, 4]


# Defines the `test_room_code_hash_membership_and_one_use_ws_ticket` callable and its typed
# interface.
async def test_room_code_hash_membership_and_one_use_ws_ticket(api: APIContext) -> None:
    # Computes and stores `host` for subsequent operations.
    host = api.current["principal"]
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/rooms",
        # Provides the `json` parameter or keyword argument.
        json={"difficulty": "normal", "idempotencyKey": "room-create-00001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text
    # Computes and stores `room` for subsequent operations.
    room = created.json()
    # Computes and stores `room_code` for subsequent operations.
    room_code = room["roomCode"]
    # Computes and stores `retried` for subsequent operations.
    retried = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/rooms",
        # Provides the `json` parameter or keyword argument.
        json={"difficulty": "normal", "idempotencyKey": "room-create-00001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retried.json()["id"] == room["id"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retried.json()["roomCode"] == room_code
    # Computes and stores `changed_retry` for subsequent operations.
    changed_retry = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/rooms",
        # Provides the `json` parameter or keyword argument.
        json={"difficulty": "hard", "idempotencyKey": "room-create-00001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert changed_retry.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert changed_retry.json()["code"] == "IDEMPOTENCY_KEY_REUSED"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert room["status"] == "waiting"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert room["members"][0]["gameId"] is None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert room["members"][0]["ready"] is False
    # Computes and stores `host_ready` for subsequent operations.
    host_ready = await api.client.post(f"/v1/rooms/{room['id']}/ready")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert host_ready.status_code == 200, host_ready.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert host_ready.json()["status"] == "waiting"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert host_ready.json()["members"][0]["ready"] is True
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `stored` for subsequent operations.
        stored = await session.get(MultiplayerRoom, uuid.UUID(room["id"]))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored.creation_request_fingerprint is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored.room_code_hash != room_code

    # Computes and stores `guest` for subsequent operations.
    guest = principal()
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = guest
    # Computes and stores `joined` for subsequent operations.
    joined = await api.client.post(f"/v1/rooms/{room_code}/join")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert joined.status_code == 200, joined.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert joined.json()["roomCode"] is None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert len(joined.json()["members"]) == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert joined.json()["status"] == "waiting"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all(member["gameId"] is None for member in joined.json()["members"])

    # Computes and stores `started` for subsequent operations.
    started = await api.client.post(f"/v1/rooms/{room['id']}/ready")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert started.status_code == 200, started.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert started.json()["status"] == "active"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all(member["ready"] for member in started.json()["members"])
    # Asserts this invariant so an unexpected test state fails immediately.
    assert sum(member["gameId"] is not None for member in started.json()["members"]) == 1
    # Computes and stores `retried_ready` for subsequent operations.
    retried_ready = await api.client.post(f"/v1/rooms/{room['id']}/ready")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retried_ready.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert retried_ready.json()["eventSequence"] == started.json()["eventSequence"]

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = host
    # Computes and stores `host_room` for subsequent operations.
    host_room = (await api.client.get(f"/v1/rooms/{room['id']}")).json()
    # Computes and stores `host_game_id` for subsequent operations.
    host_game_id = next(
        # Executes this statement as the next step in the surrounding logic.
        member["gameId"]
        # Continues the surrounding expression or operation.
        for member in host_room["members"]
        # Checks this condition before running the nested branch.
        if member["userId"] == str(host.user_id)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `blocked` for subsequent operations.
    blocked = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{host_game_id}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "duel-http-attempt-1"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert blocked.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert blocked.json()["code"] == "REALTIME_ENDPOINT_REQUIRED"

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = principal()
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.get(f"/v1/rooms/{room['id']}")).status_code == 404

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = guest
    # Computes and stores `fake_redis` for subsequent operations.
    fake_redis = FakeRedis()
    # Computes and stores `api.app.state.redis` for subsequent operations.
    api.app.state.redis = fake_redis
    # Computes and stores `api.app.state.redis_ready` for subsequent operations.
    api.app.state.redis_ready = True
    # Computes and stores `ticket_response` for subsequent operations.
    ticket_response = await api.client.post(f"/v1/rooms/{room['id']}/ws-ticket")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert ticket_response.status_code == 200, ticket_response.text
    # Computes and stores `ticket` for subsequent operations.
    ticket = ticket_response.json()["ticket"]
    # Computes and stores `key` for subsequent operations.
    key = f"mastermind:ws-ticket:{hashlib.sha256(ticket.encode()).hexdigest()}"
    # Computes and stores `stored_ticket` for subsequent operations.
    stored_ticket = await fake_redis.getdel(key)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stored_ticket is not None
    # Asserts this invariant so an unexpected test state fails immediately.
    assert json.loads(stored_ticket)["userId"] == str(guest.user_id)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert await fake_redis.getdel(key) is None

    # Computes and stores `guest_game_id` for subsequent operations.
    guest_game_id = next(
        # Executes this statement as the next step in the surrounding logic.
        member["gameId"]
        # Iterates through the supplied values for the nested operation.
        for member in started.json()["members"]
        # Checks this condition before executing the nested branch.
        if member["userId"] == str(guest.user_id)
        # Closes the multiline call, declaration, or collection started above.
    )
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.app.state.broker.subscribe(room["id"]) as events:
        # Computes and stores `abandoned` for subsequent operations.
        abandoned = await api.client.post(f"/v1/games/{guest_game_id}/abandon")
        # Asserts this invariant so an unexpected test state fails immediately.
        assert abandoned.status_code == 200, abandoned.text
        # Computes and stores `published` for subsequent operations.
        published = await anext(events)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert published["version"] == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert published["type"] == "room_completed"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert published["payload"] == {
        # Associates the `winnerId` key with its value.
        "winnerId": str(host.user_id),
        # Associates the `isTie` key with its value.
        "isTie": False,
        # Associates the `reason` key with its value.
        "reason": "forfeit",
        # Closes the multiline call, declaration, or collection started above.
    }
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `stored_event` for subsequent operations.
        stored_event = await session.find_one(
            # Supplies this required nested value.
            MultiplayerEvent,
            # Supplies this required nested value.
            {"room_id": uuid.UUID(room["id"]), "event_type": "room_completed"},
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert stored_event is not None

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = host


# Defines the `test_active_friend_challenge_allowance_is_bounded` callable and its typed interface.
async def test_active_friend_challenge_allowance_is_bounded(
    # Declares the typed `api` data field.
    api: APIContext,
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(services, "MAX_ACTIVE_CHALLENGES_PER_USER", 2)
    # Iterates through the supplied values for the nested operation.
    for title in ("First", "Second"):
        # Computes and stores `response` for subsequent operations.
        response = await api.client.post(
            # Executes this statement as the next step in the surrounding logic.
            "/v1/challenges",
            # Provides the `json` value to the surrounding call.
            json={"difficulty": "easy", "title": title},
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert response.status_code == 201
    # Computes and stores `blocked` for subsequent operations.
    blocked = await api.client.post("/v1/challenges", json={"difficulty": "easy", "title": "Third"})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert blocked.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert blocked.json()["code"] == "CHALLENGE_LIMIT_REACHED"


# Defines the `test_creator_can_return_to_private_challenge_management` callable and its typed
# interface.
async def test_creator_can_return_to_private_challenge_management(api: APIContext) -> None:
    # Computes and stores `owner` for subsequent operations.
    owner = api.current["principal"]
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/challenges",
        # Provides the `json` parameter or keyword argument.
        json={"difficulty": "normal", "title": "A private rematch"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201, created.text

    # Computes and stores `listing` for subsequent operations.
    listing = await api.client.get("/v1/challenges/mine")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert listing.status_code == 200, listing.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert listing.json()["total"] == 1
    # Computes and stores `item` for subsequent operations.
    item = listing.json()["items"][0]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert item["id"] == created.json()["id"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert item["title"] == "A private rematch"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert item["completedCount"] == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "shareCode" not in item

    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = principal()
    # Computes and stores `other_listing` for subsequent operations.
    other_listing = await api.client.get("/v1/challenges/mine")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert other_listing.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert other_listing.json()["items"] == []
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = owner


# Defines the `test_guest_friend_challenge_allowance_is_three` callable and its typed interface.
async def test_guest_friend_challenge_allowance_is_three(api: APIContext) -> None:
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = principal(anonymous=True)
    # Iterates through the supplied values for the nested operation.
    for index in range(3):
        # Computes and stores `response` for subsequent operations.
        response = await api.client.post(
            # Supplies this item to the surrounding call or collection.
            "/v1/challenges",
            # Provides the `json` parameter or keyword argument.
            json={"difficulty": "easy", "title": f"Guest challenge {index}"},
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert response.status_code == 201
    # Computes and stores `blocked` for subsequent operations.
    blocked = await api.client.post(
        # Executes this statement as the next step in the surrounding logic.
        "/v1/challenges",
        # Provides the `json` value to the surrounding call.
        json={"difficulty": "easy", "title": "Guest challenge 4"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert blocked.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert blocked.json()["code"] == "CHALLENGE_LIMIT_REACHED"
