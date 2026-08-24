# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports `io` so the module can use that dependency.
import io

# Imports `json` so the module can use that dependency.
import json

# Imports `uuid` so the module can use that dependency.
import uuid

# Imports `zipfile` so the module can use that dependency.
import zipfile

# Imports selected names from `dataclasses` for use in this module.
from dataclasses import replace

# Imports selected names from `datetime` for use in this module.
from datetime import UTC, datetime, timedelta

# Imports `mastermind_api.services as services` so the module can use that dependency.
import mastermind_api.services as services

# Imports `pytest` so the module can use that dependency.
import pytest

# Imports selected names from `mastermind_api.account` for use in this module.
from mastermind_api.account import (
    # Supplies this item to the surrounding call or collection.
    IdentityProviderError,
    # Supplies this item to the surrounding call or collection.
    get_deletion_provider,
    # Supplies this item to the surrounding call or collection.
    retry_pending_account_deletions,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_api.cache` for use in this module.
from mastermind_api.cache import LEADERBOARD_CACHE_VERSION_KEY

# Imports selected names from `mastermind_api.models` for use in this module.
from mastermind_api.models import (
    # Supplies this item to the surrounding call or collection.
    AccountDeletionRequest,
    # Supplies this item to the surrounding call or collection.
    AdminGrant,
    # Supplies this item to the surrounding call or collection.
    AuditEvent,
    # Supplies this item to the surrounding call or collection.
    DailyChallenge,
    # Supplies this item to the surrounding call or collection.
    FeatureFlag,
    # Supplies this item to the surrounding call or collection.
    FriendChallenge,
    # Supplies this item to the surrounding call or collection.
    GameSession,
    # Supplies this item to the surrounding call or collection.
    Profile,
    # Supplies this item to the surrounding call or collection.
    SupportRequest,
    # Supplies this item to the surrounding call or collection.
    UserAchievement,
    # Closes the multiline call, declaration, or collection started above.
)

# Imports selected names from `mastermind_core` for use in this module.
from mastermind_core import RULE_SET_VERSION, SCORING_VERSION, derive_daily_secret, get_preset

# Imports selected names from `sqlalchemy` for use in this module.
from sqlalchemy import func, select

# Imports selected names from `.conftest` for use in this module.
from .conftest import APIContext

# Imports selected names from `.conftest` for use in this module.
from .conftest import principal as make_principal


# Defines the `FakeLeaderboardRedis` class and its related behavior.
class FakeLeaderboardRedis:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self) -> None:
        # Computes and stores `self.values` for subsequent operations.
        self.values: dict[str, str] = {}

    # Applies `@property` to configure the declaration immediately below.
    @property
    # Defines the `version` callable and its typed interface.
    def version(self) -> int:
        # Returns this result to the caller and ends the current function.
        return int(self.values.get(LEADERBOARD_CACHE_VERSION_KEY, "0"))

    # Defines the `get` callable and its typed interface.
    async def get(self, key: str) -> str | None:
        # Returns this result to the caller and ends the current function.
        return self.values.get(key)

    # Defines the `incr` callable and its typed interface.
    async def incr(self, key: str) -> int:
        # Computes and stores `value` for subsequent operations.
        value = int(self.values.get(key, "0")) + 1
        # Executes this statement as the next step in the surrounding logic.
        self.values[key] = str(value)
        # Returns this result to the caller and ends the current function.
        return value

    # Defines the `setex` callable and its typed interface.
    async def setex(self, key: str, _seconds: int, value: str) -> None:
        # Executes this statement as the next step in the surrounding logic.
        self.values[key] = value


# Defines the `test_profile_stats_and_exact_csv_export` callable and its typed interface.
async def test_profile_stats_and_exact_csv_export(api: APIContext) -> None:
    # Computes and stores `updated` for subsequent operations.
    updated = await api.client.patch(
        # Supplies this item to the surrounding call or collection.
        "/v1/me/profile",
        # Provides the `json` parameter or keyword argument.
        json={"displayName": "Ada Lovelace", "publicLeaderboards": True},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert updated.status_code == 200, updated.text
    # Computes and stores `created` for subsequent operations.
    created = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert created.status_code == 201
    # Computes and stores `stats` for subsequent operations.
    stats = await api.client.get("/v1/me/stats")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["gamesPlayed"] == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["gamesLost"] == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["gamesAbandoned"] == 0
    # Computes and stores `exported` for subsequent operations.
    exported = await api.client.get("/v1/me/export")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert exported.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert exported.headers["content-type"] == "application/zip"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert "cipherboard-data.zip" in exported.headers["content-disposition"]
    # Acquires this managed resource and guarantees cleanup afterward.
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert set(archive.namelist()) == {
            # Supplies this item to the surrounding call or collection.
            "manifest.json",
            # Supplies this item to the surrounding call or collection.
            "profile.json",
            # Supplies this item to the surrounding call or collection.
            "games.csv",
            # Supplies this item to the surrounding call or collection.
            "attempts.csv",
            # Supplies this item to the surrounding call or collection.
            "achievements.csv",
            # Supplies this item to the surrounding call or collection.
            "challenges.csv",
            # Supplies this item to the surrounding call or collection.
            "rooms.csv",
            # Closes the multiline call, declaration, or collection started above.
        }
        # Computes and stores `profile` for subsequent operations.
        profile = json.loads(archive.read("profile.json"))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert profile["displayName"] == "Ada Lovelace"
        # Computes and stores `payload` for subsequent operations.
        payload = b"".join(archive.read(name) for name in archive.namelist())
        # Asserts this invariant so an unexpected test state fails immediately.
        assert b"encrypted_secret" not in payload
        # Asserts this invariant so an unexpected test state fails immediately.
        assert b"secret_nonce" not in payload
        # Asserts this invariant so an unexpected test state fails immediately.
        assert b"creation_idempotency_key" not in payload


# Defines the `test_profile_privacy_changes_refresh_public_and_daily_leaderboards` callable and its
# typed interface.
async def test_profile_privacy_changes_refresh_public_and_daily_leaderboards(
    # Declares the typed `api` data field.
    api: APIContext,
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `redis` for subsequent operations.
    redis = FakeLeaderboardRedis()
    # Computes and stores `api.app.state.redis` for subsequent operations.
    api.app.state.redis = redis
    # Computes and stores `api.app.state.redis_ready` for subsequent operations.
    api.app.state.redis_ready = True
    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))

    # Computes and stores `updated` for subsequent operations.
    updated = await api.client.patch(
        # Supplies this item to the surrounding call or collection.
        "/v1/me/profile",
        # Provides the `json` parameter or keyword argument.
        json={"displayName": "Ada Lovelace", "publicLeaderboards": True},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert updated.status_code == 200, updated.text

    # Computes and stores `solo` for subsequent operations.
    solo = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    # Computes and stores `solo_win` for subsequent operations.
    solo_win = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{solo.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "privacy-solo-win-0001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert solo_win.status_code == 200 and solo_win.json()["status"] == "won"

    # Computes and stores `daily_definition` for subsequent operations.
    daily_definition = await api.client.get("/v1/daily")
    # Computes and stores `daily` for subsequent operations.
    daily = await api.client.post("/v1/daily/start")
    # Computes and stores `daily_secret` for subsequent operations.
    daily_secret = derive_daily_secret(
        # Calls `datetime.fromisoformat` with the supplied values.
        datetime.fromisoformat(daily_definition.json()["date"]).date(),
        # Calls `get_preset` with the supplied values.
        get_preset("normal"),
        # Supplies this item to the surrounding call or collection.
        b"d" * 32,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `daily_win` for subsequent operations.
    daily_win = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{daily.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list(daily_secret), "idempotencyKey": "privacy-daily-win-001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert daily_win.status_code == 200 and daily_win.json()["status"] == "won"

    # Computes and stores `endpoints` for subsequent operations.
    endpoints = ("/v1/leaderboards", "/v1/daily/leaderboard")
    # Iterates through the supplied values for the nested operation.
    for endpoint in endpoints:
        # Computes and stores `leaderboard` for subsequent operations.
        leaderboard = await api.client.get(endpoint)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert leaderboard.status_code == 200, leaderboard.text
        # Asserts this invariant so an unexpected test state fails immediately.
        assert leaderboard.json()["total"] >= 1
        # Asserts this invariant so an unexpected test state fails immediately.
        assert {item["displayName"] for item in leaderboard.json()["items"]} == {"Ada Lovelace"}

    # Computes and stores `prior_version` for subsequent operations.
    prior_version = redis.version
    # Computes and stores `renamed` for subsequent operations.
    renamed = await api.client.patch(
        # Supplies this item to the surrounding call or collection.
        "/v1/me/profile",
        # Provides the `json` parameter or keyword argument.
        json={"displayName": "Grace Hopper"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert renamed.status_code == 200, renamed.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redis.version == prior_version + 1
    # Iterates through the supplied values for the nested operation.
    for endpoint in endpoints:
        # Computes and stores `leaderboard` for subsequent operations.
        leaderboard = await api.client.get(endpoint)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert {item["displayName"] for item in leaderboard.json()["items"]} == {"Grace Hopper"}

    # Computes and stores `prior_version` for subsequent operations.
    prior_version = redis.version
    # Computes and stores `opted_out` for subsequent operations.
    opted_out = await api.client.patch(
        # Supplies this item to the surrounding call or collection.
        "/v1/me/profile",
        # Provides the `json` parameter or keyword argument.
        json={"publicLeaderboards": False},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert opted_out.status_code == 200, opted_out.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redis.version == prior_version + 1
    # Iterates through the supplied values for the nested operation.
    for endpoint in endpoints:
        # Computes and stores `leaderboard` for subsequent operations.
        leaderboard = await api.client.get(endpoint)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert leaderboard.json()["items"] == []
        # Asserts this invariant so an unexpected test state fails immediately.
        assert leaderboard.json()["total"] == 0
        # Asserts this invariant so an unexpected test state fails immediately.
        assert leaderboard.json()["currentUserRank"] is None


# Defines the `test_official_stats_exclude_nonofficial_and_ineligible_wins` callable and its typed
# interface.
async def test_official_stats_exclude_nonofficial_and_ineligible_wins(api: APIContext) -> None:
    # Waits for this asynchronous operation to complete.
    await api.client.get("/v1/me/profile")
    # Computes and stores `now` for subsequent operations.
    now = datetime.now(UTC)
    # Computes and stores `cases` for subsequent operations.
    cases = (
        # Supplies this item to the surrounding call or collection.
        ("solo", "eligible", 100, 30),
        # Supplies this item to the surrounding call or collection.
        ("daily", "eligible", 200, 20),
        # Supplies this item to the surrounding call or collection.
        ("practice", "eligible", 900, 1),
        # Supplies this item to the surrounding call or collection.
        ("pass_and_play", "eligible", 800, 2),
        # Supplies this item to the surrounding call or collection.
        ("friend_challenge", "eligible", 700, 3),
        # Supplies this item to the surrounding call or collection.
        ("duel", "eligible", 600, 4),
        # Supplies this item to the surrounding call or collection.
        ("solo", "unranked", 500, 5),
        # Supplies this item to the surrounding call or collection.
        ("solo", "invalidated", 400, 6),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `config` for subsequent operations.
    config = get_preset("normal")
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Calls `session.add_all` with the supplied values.
        session.add_all(
            # Begins the nested block or multiline expression completed below.
            [
                # Calls `GameSession` with the supplied values.
                GameSession(
                    # Provides the `public_id` parameter or keyword argument.
                    public_id=f"stats-{index}",
                    # Provides the `owner_id` parameter or keyword argument.
                    owner_id=api.current["principal"].user_id,
                    # Provides the `mode` parameter or keyword argument.
                    mode=mode,
                    # Provides the `difficulty` parameter or keyword argument.
                    difficulty="normal",
                    # Provides the `config` parameter or keyword argument.
                    config=config.to_dict(),
                    # Provides the `status` parameter or keyword argument.
                    status="won",
                    # Provides the `rule_set_version` parameter or keyword argument.
                    rule_set_version=RULE_SET_VERSION,
                    # Provides the `scoring_version` parameter or keyword argument.
                    scoring_version=SCORING_VERSION,
                    # Provides the `encrypted_secret` parameter or keyword argument.
                    encrypted_secret=b"ciphertext",
                    # Provides the `secret_nonce` parameter or keyword argument.
                    secret_nonce=b"nonce",
                    # Provides the `secret_key_version` parameter or keyword argument.
                    secret_key_version="v1",
                    # Provides the `attempts_used` parameter or keyword argument.
                    attempts_used=1,
                    # Provides the `maximum_attempts` parameter or keyword argument.
                    maximum_attempts=config.max_attempts,
                    # Provides the `started_at` parameter or keyword argument.
                    started_at=now - timedelta(seconds=elapsed),
                    # Provides the `expires_at` parameter or keyword argument.
                    expires_at=now + timedelta(days=1),
                    # Provides the `completed_at` parameter or keyword argument.
                    completed_at=now,
                    # Provides the `elapsed_seconds` parameter or keyword argument.
                    elapsed_seconds=elapsed,
                    # Provides the `final_score` parameter or keyword argument.
                    final_score=score,
                    # Provides the `score_breakdown` parameter or keyword argument.
                    score_breakdown={},
                    # Provides the `ranked_eligibility` parameter or keyword argument.
                    ranked_eligibility=eligibility,
                    # Closes the multiline call, declaration, or collection started above.
                )
                # Iterates through the supplied values for the nested operation.
                for index, (mode, eligibility, score, elapsed) in enumerate(cases)
                # Closes the multiline call, declaration, or collection started above.
            ]
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `stats` for subsequent operations.
    stats = await api.client.get("/v1/me/stats")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.status_code == 200, stats.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["gamesWon"] == len(cases)
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["bestScoreByDifficulty"] == {"normal": 200}
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["fastestEligibleSolve"] == 20


# Defines the `FlakyDeletionProvider` class and its related behavior.
class FlakyDeletionProvider:
    # Defines the `__init__` callable and its typed interface.
    def __init__(self) -> None:
        # Computes and stores `self.calls` for subsequent operations.
        self.calls = 0
        # Computes and stores `self.revocations` for subsequent operations.
        self.revocations = 0
        # Computes and stores `self.events` for subsequent operations.
        self.events: list[str] = []

    # Defines the `revoke_sessions` callable and its typed interface.
    async def revoke_sessions(self, access_token: str) -> None:
        # Asserts this invariant so an unexpected test state fails immediately.
        assert access_token == "test-access-token"
        # Executes this statement as the next step in the surrounding logic.
        self.revocations += 1
        # Calls `self.events.append` with the supplied values.
        self.events.append("revoke")

    # Defines the `delete_user` callable and its typed interface.
    async def delete_user(self, _user_id: uuid.UUID) -> None:
        # Executes this statement as the next step in the surrounding logic.
        self.calls += 1
        # Calls `self.events.append` with the supplied values.
        self.events.append("delete")
        # Checks this condition before executing the nested branch.
        if self.calls == 1:
            # Raises this exception to report an invalid or failed operation.
            raise IdentityProviderError("provider_unavailable")


# Defines the `test_account_deletion_retries_provider_before_success` callable and its typed
# interface.
async def test_account_deletion_retries_provider_before_success(api: APIContext) -> None:
    # Computes and stores `provider` for subsequent operations.
    provider = FlakyDeletionProvider()
    # Executes this statement as the next step in the surrounding logic.
    api.app.dependency_overrides[get_deletion_provider] = lambda: provider
    # Waits for this asynchronous operation to complete.
    await api.client.get("/v1/me/profile")
    # Computes and stores `challenge_response` for subsequent operations.
    challenge_response = await api.client.post(
        # Executes this statement as the next step in the surrounding logic.
        "/v1/challenges",
        # Provides the `json` value to the surrounding call.
        json={"difficulty": "easy", "title": "Remove this title"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert challenge_response.status_code == 201
    # Computes and stores `support_response` for subsequent operations.
    support_response = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/support",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `topic` key with its value.
            "topic": "privacy",
            # Associates the `replyEmail` key with its value.
            "replyEmail": "private@example.com",
            # Associates the `message` key with its value.
            "message": "Please remove this correspondence with the account.",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert support_response.status_code == 202
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Calls `session.add` with the supplied values.
        session.add(
            # Calls `UserAchievement` with the supplied values.
            UserAchievement(
                # Provides the `user_id` parameter or keyword argument.
                user_id=api.current["principal"].user_id,
                # Provides the `achievement_key` parameter or keyword argument.
                achievement_key="first_break",
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Computes and stores `redis` for subsequent operations.
    redis = FakeLeaderboardRedis()
    # Computes and stores `api.app.state.redis` for subsequent operations.
    api.app.state.redis = redis
    # Computes and stores `headers` for subsequent operations.
    headers = {"Authorization": "Bearer test-access-token"}
    # Computes and stores `first` for subsequent operations.
    first = await api.client.request(
        # Executes this statement as the next step in the surrounding logic.
        "DELETE",
        # Supplies this string to the surrounding call or collection.
        "/v1/me",
        # Provides the `headers` value to the surrounding call.
        headers=headers,
        # Provides the `json` value to the surrounding call.
        json={"confirmation": "DELETE"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.status_code == 503
    # Asserts this invariant so an unexpected test state fails immediately.
    assert first.json()["code"] == "ACCOUNT_DELETION_PENDING"
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redis.version == 1
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `profile` for subsequent operations.
        profile = await session.get(Profile, api.current["principal"].user_id)
        # Computes and stores `deletion` for subsequent operations.
        deletion = await session.scalar(select(AccountDeletionRequest))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert profile is not None and profile.deleted_at is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert profile.display_name is None and profile.public_leaderboards is False
        # Asserts this invariant so an unexpected test state fails immediately.
        assert profile.is_anonymous is True
        # Asserts this invariant so an unexpected test state fails immediately.
        assert deletion is not None and deletion.status == "provider_failed"
        # Computes and stores `challenge` for subsequent operations.
        challenge = await session.scalar(select(FriendChallenge))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert challenge is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert challenge.title is None and challenge.revoked_at is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.scalar(select(func.count(SupportRequest.id))) == 0
        # Asserts this invariant so an unexpected test state fails immediately.
        assert await session.scalar(select(func.count(UserAchievement.id))) == 0
    # Computes and stores `second` for subsequent operations.
    second = await api.client.request(
        # Executes this statement as the next step in the surrounding logic.
        "DELETE",
        # Supplies this string to the surrounding call or collection.
        "/v1/me",
        # Provides the `headers` value to the surrounding call.
        headers=headers,
        # Provides the `json` value to the surrounding call.
        json={"confirmation": "DELETE"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert second.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert second.json() == {"deleted": True}
    # Computes and stores `third` for subsequent operations.
    third = await api.client.request(
        # Executes this statement as the next step in the surrounding logic.
        "DELETE",
        # Supplies this string to the surrounding call or collection.
        "/v1/me",
        # Provides the `headers` value to the surrounding call.
        headers=headers,
        # Provides the `json` value to the surrounding call.
        json={"confirmation": "DELETE"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert third.status_code == 200
    # Asserts this invariant so an unexpected test state fails immediately.
    assert provider.calls == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert provider.revocations == 2
    # Asserts this invariant so an unexpected test state fails immediately.
    assert provider.events == ["revoke", "delete", "revoke", "delete"]
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `deletion` for subsequent operations.
        deletion = await session.scalar(select(AccountDeletionRequest))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert deletion is not None and deletion.status == "completed"


# Defines the `test_guest_export_and_account_deletion_require_upgrade` callable and its typed
# interface.
async def test_guest_export_and_account_deletion_require_upgrade(api: APIContext) -> None:
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = make_principal(anonymous=True)
    # Computes and stores `exported` for subsequent operations.
    exported = await api.client.get("/v1/me/export")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert exported.status_code == 403
    # Asserts this invariant so an unexpected test state fails immediately.
    assert exported.json()["code"] == "ACCOUNT_UPGRADE_REQUIRED"
    # Computes and stores `deleted` for subsequent operations.
    deleted = await api.client.request(
        # Supplies this item to the surrounding call or collection.
        "DELETE",
        # Supplies this item to the surrounding call or collection.
        "/v1/me",
        # Provides the `headers` parameter or keyword argument.
        headers={"Authorization": "Bearer anonymous-access-token"},
        # Provides the `json` parameter or keyword argument.
        json={"confirmation": "DELETE"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert deleted.status_code == 403
    # Asserts this invariant so an unexpected test state fails immediately.
    assert deleted.json()["code"] == "ACCOUNT_UPGRADE_REQUIRED"


# Defines the `test_account_deletion_requires_exact_confirmation_and_recent_auth` callable and its
# typed interface.
async def test_account_deletion_requires_exact_confirmation_and_recent_auth(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `missing` for subsequent operations.
    missing = await api.client.delete("/v1/me")
    # Computes and stores `wrong` for subsequent operations.
    wrong = await api.client.request("DELETE", "/v1/me", json={"confirmation": "delete"})
    # Asserts this invariant so an unexpected test state fails immediately.
    assert missing.status_code == 422
    # Asserts this invariant so an unexpected test state fails immediately.
    assert wrong.status_code == 422

    # Computes and stores `current` for subsequent operations.
    current = api.current["principal"]
    # Begins the nested block or multiline expression completed below.
    api.current["principal"] = replace(
        # Supplies this item to the surrounding call or collection.
        current,
        # Provides the `authenticated_at` parameter or keyword argument.
        authenticated_at=datetime.now(UTC) - timedelta(hours=1),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `stale` for subsequent operations.
    stale = await api.client.request(
        # Supplies this item to the surrounding call or collection.
        "DELETE",
        # Supplies this item to the surrounding call or collection.
        "/v1/me",
        # Provides the `headers` parameter or keyword argument.
        headers={"Authorization": "Bearer stale-access-token"},
        # Provides the `json` parameter or keyword argument.
        json={"confirmation": "DELETE"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stale.status_code == 401
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stale.json()["code"] == "RECENT_AUTH_REQUIRED"


# Defines the `test_daily_stats_use_challenge_date_and_expire_stale_streak` callable and its typed
# interface.
async def test_daily_stats_use_challenge_date_and_expire_stale_streak(
    # Declares the typed `api` data field.
    api: APIContext,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `started` for subsequent operations.
    started = await api.client.post("/v1/daily/start")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert started.status_code == 200, started.text
    # Computes and stores `old_day` for subsequent operations.
    old_day = datetime.now(UTC).date() - timedelta(days=5)
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `game` for subsequent operations.
        game = await session.scalar(
            # Calls `select` with the supplied values.
            select(GameSession).where(GameSession.public_id == started.json()["id"])
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert game is not None and game.daily_challenge_id is not None
        # Computes and stores `daily` for subsequent operations.
        daily = await session.get(DailyChallenge, game.daily_challenge_id)
        # Asserts this invariant so an unexpected test state fails immediately.
        assert daily is not None
        # Computes and stores `daily.challenge_date` for subsequent operations.
        daily.challenge_date = old_day
        # Computes and stores `game.status` for subsequent operations.
        game.status = "lost"
        # Computes and stores `game.completed_at` for subsequent operations.
        game.completed_at = datetime.now(UTC)
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `stats` for subsequent operations.
    stats = await api.client.get("/v1/me/stats")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.status_code == 200, stats.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["dailyCompletionHistory"] == [old_day.isoformat()]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["dailyStreak"] == 0
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stats.json()["achievementProgress"] == {"logic_week": {"current": 1, "target": 7}}


# Defines the `test_deletion_worker_completes_queued_provider_failure` callable and its typed
# interface.
async def test_deletion_worker_completes_queued_provider_failure(api: APIContext) -> None:
    # Computes and stores `user_id` for subsequent operations.
    user_id = uuid.uuid4()
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Calls `session.add` with the supplied values.
        session.add(
            # Calls `AccountDeletionRequest` with the supplied values.
            AccountDeletionRequest(
                # Provides the `user_id` parameter or keyword argument.
                user_id=user_id,
                # Provides the `status` parameter or keyword argument.
                status="provider_failed",
                # Provides the `provider_attempts` parameter or keyword argument.
                provider_attempts=1,
                # Provides the `last_error_code` parameter or keyword argument.
                last_error_code="provider_unavailable",
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Defines the `AvailableProvider` class and its related behavior.
    class AvailableProvider:
        # Defines the `__init__` callable and its typed interface.
        def __init__(self) -> None:
            # Computes and stores `self.deleted` for subsequent operations.
            self.deleted: list[uuid.UUID] = []

        # Defines the `delete_user` callable and its typed interface.
        async def delete_user(self, target_id: uuid.UUID) -> None:
            # Calls `self.deleted.append` with the supplied values.
            self.deleted.append(target_id)

    # Computes and stores `provider` for subsequent operations.
    provider = AvailableProvider()
    # Computes and stores `completed` for subsequent operations.
    completed = await retry_pending_account_deletions(api.sessions, provider)  # type: ignore[arg-type]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert completed == 1
    # Asserts this invariant so an unexpected test state fails immediately.
    assert provider.deleted == [user_id]
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `deletion` for subsequent operations.
        deletion = await session.scalar(
            # Calls `select` with the supplied values.
            select(AccountDeletionRequest).where(AccountDeletionRequest.user_id == user_id)
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert deletion is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert deletion.status == "completed"
        # Asserts this invariant so an unexpected test state fails immediately.
        assert deletion.provider_attempts == 2
        # Asserts this invariant so an unexpected test state fails immediately.
        assert deletion.last_error_code is None


# Defines the `test_admin_uses_database_grant_recent_auth_and_audits_mutation` callable and its
# typed interface.
async def test_admin_uses_database_grant_recent_auth_and_audits_mutation(api: APIContext) -> None:
    # Waits for this asynchronous operation to complete.
    await api.client.get("/v1/me/profile")
    # Computes and stores `current_id` for subsequent operations.
    current_id = api.current["principal"].user_id
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = replace(make_principal(current_id), assurance_level="aal2")
    # Computes and stores `denied` for subsequent operations.
    denied = await api.client.get("/v1/admin/summary")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert denied.status_code == 403
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Calls `session.add` with the supplied values.
        session.add(AdminGrant(user_id=api.current["principal"].user_id))
        # Waits for this asynchronous operation to complete.
        await session.commit()
    # Begins the nested block or multiline expression completed below.
    api.current["principal"] = replace(
        # Calls `make_principal` with the supplied values.
        make_principal(current_id, anonymous=True),
        # Provides the `assurance_level` value to the surrounding call.
        assurance_level="aal2",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.get("/v1/admin/summary")).status_code == 403
    # Begins the nested block or multiline expression completed below.
    api.current["principal"] = replace(
        # Calls `make_principal` with the supplied values.
        make_principal(current_id),
        # Provides the `assurance_level` value to the surrounding call.
        assurance_level="aal2",
        # Provides the `session_id` value to the surrounding call.
        session_id=None,
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.get("/v1/admin/summary")).status_code == 401
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = make_principal(current_id)
    # Computes and stores `mfa_denied` for subsequent operations.
    mfa_denied = await api.client.get("/v1/admin/summary")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert mfa_denied.status_code == 401
    # Asserts this invariant so an unexpected test state fails immediately.
    assert mfa_denied.json()["code"] == "MFA_REQUIRED"
    # Begins the nested block or multiline expression completed below.
    api.current["principal"] = type(api.current["principal"])(
        # Provides the `user_id` parameter or keyword argument.
        user_id=current_id,
        # Provides the `is_anonymous` parameter or keyword argument.
        is_anonymous=False,
        # Provides the `session_id` parameter or keyword argument.
        session_id="old-session",
        # Provides the `issued_at` parameter or keyword argument.
        issued_at=datetime.now(UTC) - timedelta(hours=1),
        # Provides the `authenticated_at` parameter or keyword argument.
        authenticated_at=datetime.now(UTC) - timedelta(hours=1),
        # Provides the `assurance_level` parameter or keyword argument.
        assurance_level="aal2",
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `stale` for subsequent operations.
    stale = await api.client.get("/v1/admin/summary")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stale.status_code == 401
    # Asserts this invariant so an unexpected test state fails immediately.
    assert stale.json()["code"] == "RECENT_AUTH_REQUIRED"
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = replace(make_principal(current_id), assurance_level="aal2")
    # Computes and stores `summary` for subsequent operations.
    summary = await api.client.get("/v1/admin/summary")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert summary.status_code == 200, summary.text
    # Iterates through the supplied values for the nested operation.
    for route in ("games", "profiles", "rooms", "challenges", "leaderboard-review"):
        # Computes and stores `listing` for subsequent operations.
        listing = await api.client.get(f"/v1/admin/{route}")
        # Asserts this invariant so an unexpected test state fails immediately.
        assert listing.status_code == 200, listing.text
        # Asserts this invariant so an unexpected test state fails immediately.
        assert {"items", "page", "pageSize", "total"}.issubset(listing.json())
    # Computes and stores `games` for subsequent operations.
    games = (await api.client.get("/v1/admin/games")).json()["items"]
    # Asserts this invariant so an unexpected test state fails immediately.
    assert all("secret" not in game and "attempts" not in game for game in games)
    # Computes and stores `self_moderation` for subsequent operations.
    self_moderation = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/admin/profiles/{current_id}/moderate",
        # Provides the `json` parameter or keyword argument.
        json={"reason": "Must require a second administrator", "enabled": True},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert self_moderation.status_code == 409
    # Asserts this invariant so an unexpected test state fails immediately.
    assert self_moderation.json()["code"] == "ADMIN_SELF_MODERATION_FORBIDDEN"
    # Computes and stores `changed` for subsequent operations.
    changed = await api.client.patch(
        # Executes this statement as the next step in the surrounding logic.
        "/v1/admin/flags/daily",
        # Provides the `json` value to the surrounding call.
        json={"reason": "Incident mitigation", "enabled": False},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert changed.status_code == 200
    # Computes and stores `disabled` for subsequent operations.
    disabled = await api.client.get("/v1/daily")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert disabled.status_code == 503
    # Asserts this invariant so an unexpected test state fails immediately.
    assert disabled.json()["code"] == "FEATURE_DISABLED"
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `flag` for subsequent operations.
        flag = await session.get(FeatureFlag, "daily")
        # Computes and stores `audit` for subsequent operations.
        audit = await session.scalar(
            # Calls `select` with the supplied values.
            select(AuditEvent).where(AuditEvent.action == "feature_flag.updated")
            # Closes the multiline call, declaration, or collection started above.
        )
        # Asserts this invariant so an unexpected test state fails immediately.
        assert flag is not None and flag.enabled is False
        # Asserts this invariant so an unexpected test state fails immediately.
        assert audit is not None and audit.actor_id == api.current["principal"].user_id


# Defines the `test_admin_moderation_refreshes_cached_leaderboard_privacy` callable and its typed
# interface.
async def test_admin_moderation_refreshes_cached_leaderboard_privacy(
    # Declares the typed `api` data field.
    api: APIContext,
    # Declares the typed `monkeypatch` data field.
    monkeypatch: pytest.MonkeyPatch,
    # Completes the signature and declares the callable return type.
) -> None:
    # Computes and stores `redis` for subsequent operations.
    redis = FakeLeaderboardRedis()
    # Computes and stores `api.app.state.redis` for subsequent operations.
    api.app.state.redis = redis
    # Computes and stores `api.app.state.redis_ready` for subsequent operations.
    api.app.state.redis_ready = True
    # Configures this test double for the scenario being verified.
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))

    # Computes and stores `target` for subsequent operations.
    target = api.current["principal"]
    # Computes and stores `updated` for subsequent operations.
    updated = await api.client.patch(
        # Supplies this item to the surrounding call or collection.
        "/v1/me/profile",
        # Provides the `json` parameter or keyword argument.
        json={"displayName": "Visible Player", "publicLeaderboards": True},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert updated.status_code == 200, updated.text
    # Computes and stores `game` for subsequent operations.
    game = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    # Computes and stores `won` for subsequent operations.
    won = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/games/{game.json()['id']}/attempts",
        # Provides the `json` parameter or keyword argument.
        json={"guess": list("RBGY"), "idempotencyKey": "moderation-win-00001"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert won.status_code == 200 and won.json()["status"] == "won"

    # Computes and stores `admin` for subsequent operations.
    admin = replace(make_principal(), assurance_level="aal2")
    # Executes this statement as the next step in the surrounding logic.
    api.current["principal"] = admin
    # Asserts this invariant so an unexpected test state fails immediately.
    assert (await api.client.get("/v1/me/profile")).status_code == 200
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Calls `session.add` with the supplied values.
        session.add(AdminGrant(user_id=admin.user_id))
        # Waits for this asynchronous operation to complete.
        await session.commit()

    # Computes and stores `cached` for subsequent operations.
    cached = await api.client.get("/v1/leaderboards")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert cached.status_code == 200, cached.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert cached.json()["items"][0]["displayName"] == "Visible Player"

    # Computes and stores `prior_version` for subsequent operations.
    prior_version = redis.version
    # Computes and stores `banned` for subsequent operations.
    banned = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/admin/profiles/{target.user_id}/moderate",
        # Provides the `json` parameter or keyword argument.
        json={"reason": "Confirmed leaderboard abuse", "enabled": True},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert banned.status_code == 200, banned.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redis.version == prior_version + 1
    # Computes and stores `hidden` for subsequent operations.
    hidden = await api.client.get("/v1/leaderboards")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert hidden.json()["items"] == []

    # Computes and stores `prior_version` for subsequent operations.
    prior_version = redis.version
    # Computes and stores `restored` for subsequent operations.
    restored = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        f"/v1/admin/profiles/{target.user_id}/moderate",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `reason` key with its value.
            "reason": "Appeal accepted after review",
            # Associates the `enabled` key with its value.
            "enabled": False,
            # Associates the `displayName` key with its value.
            "displayName": "Reviewed Player",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert restored.status_code == 200, restored.text
    # Asserts this invariant so an unexpected test state fails immediately.
    assert redis.version == prior_version + 1
    # Computes and stores `refreshed` for subsequent operations.
    refreshed = await api.client.get("/v1/leaderboards")
    # Asserts this invariant so an unexpected test state fails immediately.
    assert refreshed.json()["items"][0]["displayName"] == "Reviewed Player"


# Defines the `test_support_request_is_validated_rate_limited_and_minimal` callable and its typed
# interface.
async def test_support_request_is_validated_rate_limited_and_minimal(api: APIContext) -> None:
    # Computes and stores `invalid` for subsequent operations.
    invalid = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/support",
        # Provides the `json` parameter or keyword argument.
        json={"topic": "other", "replyEmail": "not-an-email", "message": "short"},
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert invalid.status_code == 422
    # Computes and stores `accepted` for subsequent operations.
    accepted = await api.client.post(
        # Supplies this item to the surrounding call or collection.
        "/v1/support",
        # Computes and stores `json` for subsequent operations.
        json={
            # Associates the `topic` key with its value.
            "topic": "accessibility",
            # Associates the `replyEmail` key with its value.
            "replyEmail": "player@example.com",
            # Associates the `message` key with its value.
            "message": "Keyboard focus disappears after I submit a row.",
            # Closes the multiline call, declaration, or collection started above.
        },
        # Closes the multiline call, declaration, or collection started above.
    )
    # Asserts this invariant so an unexpected test state fails immediately.
    assert accepted.status_code == 202, accepted.text
    # Acquires this asynchronous managed resource for the nested operation.
    async with api.sessions() as session:
        # Computes and stores `support` for subsequent operations.
        support = await session.scalar(select(SupportRequest))
        # Asserts this invariant so an unexpected test state fails immediately.
        assert support is not None
        # Asserts this invariant so an unexpected test state fails immediately.
        assert support.user_id == api.current["principal"].user_id
        # Asserts this invariant so an unexpected test state fails immediately.
        assert "ip" not in SupportRequest.__table__.columns
