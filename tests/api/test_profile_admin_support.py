from __future__ import annotations

import io
import json
import uuid
import zipfile
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import mastermind_api.services as services
import pytest
from mastermind_api.account import (
    IdentityProviderError,
    get_deletion_provider,
    retry_pending_account_deletions,
)
from mastermind_api.cache import LEADERBOARD_CACHE_VERSION_KEY
from mastermind_api.models import (
    AccountDeletionRequest,
    AdminGrant,
    AuditEvent,
    DailyChallenge,
    FeatureFlag,
    FriendChallenge,
    GameSession,
    Profile,
    SupportRequest,
    UserAchievement,
)
from mastermind_core import RULE_SET_VERSION, SCORING_VERSION, derive_daily_secret, get_preset
from sqlalchemy import func, select

from .conftest import APIContext
from .conftest import principal as make_principal


class FakeLeaderboardRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    @property
    def version(self) -> int:
        return int(self.values.get(LEADERBOARD_CACHE_VERSION_KEY, "0"))

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def incr(self, key: str) -> int:
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    async def setex(self, key: str, _seconds: int, value: str) -> None:
        self.values[key] = value


async def test_profile_stats_and_exact_csv_export(api: APIContext) -> None:
    updated = await api.client.patch(
        "/v1/me/profile",
        json={"displayName": "Ada Lovelace", "publicLeaderboards": True},
    )
    assert updated.status_code == 200, updated.text
    created = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    assert created.status_code == 201
    stats = await api.client.get("/v1/me/stats")
    assert stats.status_code == 200
    assert stats.json()["gamesPlayed"] == 0
    assert stats.json()["gamesLost"] == 0
    assert stats.json()["gamesAbandoned"] == 0
    exported = await api.client.get("/v1/me/export")
    assert exported.status_code == 200
    assert exported.headers["content-type"] == "application/zip"
    assert "cipherboard-data.zip" in exported.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        assert set(archive.namelist()) == {
            "manifest.json",
            "profile.json",
            "games.csv",
            "attempts.csv",
            "achievements.csv",
            "challenges.csv",
            "rooms.csv",
        }
        profile = json.loads(archive.read("profile.json"))
        assert profile["displayName"] == "Ada Lovelace"
        payload = b"".join(archive.read(name) for name in archive.namelist())
        assert b"encrypted_secret" not in payload
        assert b"secret_nonce" not in payload
        assert b"creation_idempotency_key" not in payload


async def test_profile_privacy_changes_refresh_public_and_daily_leaderboards(
    api: APIContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = FakeLeaderboardRedis()
    api.app.state.redis = redis
    api.app.state.redis_ready = True
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))

    updated = await api.client.patch(
        "/v1/me/profile",
        json={"displayName": "Ada Lovelace", "publicLeaderboards": True},
    )
    assert updated.status_code == 200, updated.text

    solo = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    solo_win = await api.client.post(
        f"/v1/games/{solo.json()['id']}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "privacy-solo-win-0001"},
    )
    assert solo_win.status_code == 200 and solo_win.json()["status"] == "won"

    daily_definition = await api.client.get("/v1/daily")
    daily = await api.client.post("/v1/daily/start")
    daily_secret = derive_daily_secret(
        datetime.fromisoformat(daily_definition.json()["date"]).date(),
        get_preset("normal"),
        b"d" * 32,
    )
    daily_win = await api.client.post(
        f"/v1/games/{daily.json()['id']}/attempts",
        json={"guess": list(daily_secret), "idempotencyKey": "privacy-daily-win-001"},
    )
    assert daily_win.status_code == 200 and daily_win.json()["status"] == "won"

    endpoints = ("/v1/leaderboards", "/v1/daily/leaderboard")
    for endpoint in endpoints:
        leaderboard = await api.client.get(endpoint)
        assert leaderboard.status_code == 200, leaderboard.text
        assert leaderboard.json()["total"] >= 1
        assert {item["displayName"] for item in leaderboard.json()["items"]} == {"Ada Lovelace"}

    prior_version = redis.version
    renamed = await api.client.patch(
        "/v1/me/profile",
        json={"displayName": "Grace Hopper"},
    )
    assert renamed.status_code == 200, renamed.text
    assert redis.version == prior_version + 1
    for endpoint in endpoints:
        leaderboard = await api.client.get(endpoint)
        assert {item["displayName"] for item in leaderboard.json()["items"]} == {"Grace Hopper"}

    prior_version = redis.version
    opted_out = await api.client.patch(
        "/v1/me/profile",
        json={"publicLeaderboards": False},
    )
    assert opted_out.status_code == 200, opted_out.text
    assert redis.version == prior_version + 1
    for endpoint in endpoints:
        leaderboard = await api.client.get(endpoint)
        assert leaderboard.json()["items"] == []
        assert leaderboard.json()["total"] == 0
        assert leaderboard.json()["currentUserRank"] is None


async def test_official_stats_exclude_nonofficial_and_ineligible_wins(api: APIContext) -> None:
    await api.client.get("/v1/me/profile")
    now = datetime.now(UTC)
    cases = (
        ("solo", "eligible", 100, 30),
        ("daily", "eligible", 200, 20),
        ("practice", "eligible", 900, 1),
        ("pass_and_play", "eligible", 800, 2),
        ("friend_challenge", "eligible", 700, 3),
        ("duel", "eligible", 600, 4),
        ("solo", "unranked", 500, 5),
        ("solo", "invalidated", 400, 6),
    )
    config = get_preset("normal")
    async with api.sessions() as session:
        session.add_all(
            [
                GameSession(
                    public_id=f"stats-{index}",
                    owner_id=api.current["principal"].user_id,
                    mode=mode,
                    difficulty="normal",
                    config=config.to_dict(),
                    status="won",
                    rule_set_version=RULE_SET_VERSION,
                    scoring_version=SCORING_VERSION,
                    encrypted_secret=b"ciphertext",
                    secret_nonce=b"nonce",
                    secret_key_version="v1",
                    attempts_used=1,
                    maximum_attempts=config.max_attempts,
                    started_at=now - timedelta(seconds=elapsed),
                    expires_at=now + timedelta(days=1),
                    completed_at=now,
                    elapsed_seconds=elapsed,
                    final_score=score,
                    score_breakdown={},
                    ranked_eligibility=eligibility,
                )
                for index, (mode, eligibility, score, elapsed) in enumerate(cases)
            ]
        )
        await session.commit()

    stats = await api.client.get("/v1/me/stats")
    assert stats.status_code == 200, stats.text
    assert stats.json()["gamesWon"] == len(cases)
    assert stats.json()["bestScoreByDifficulty"] == {"normal": 200}
    assert stats.json()["fastestEligibleSolve"] == 20


class FlakyDeletionProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.revocations = 0
        self.events: list[str] = []

    async def revoke_sessions(self, access_token: str) -> None:
        assert access_token == "test-access-token"
        self.revocations += 1
        self.events.append("revoke")

    async def delete_user(self, _user_id: uuid.UUID) -> None:
        self.calls += 1
        self.events.append("delete")
        if self.calls == 1:
            raise IdentityProviderError("provider_unavailable")


async def test_account_deletion_retries_provider_before_success(api: APIContext) -> None:
    provider = FlakyDeletionProvider()
    api.app.dependency_overrides[get_deletion_provider] = lambda: provider
    await api.client.get("/v1/me/profile")
    challenge_response = await api.client.post(
        "/v1/challenges", json={"difficulty": "easy", "title": "Remove this title"}
    )
    assert challenge_response.status_code == 201
    support_response = await api.client.post(
        "/v1/support",
        json={
            "topic": "privacy",
            "replyEmail": "private@example.com",
            "message": "Please remove this correspondence with the account.",
        },
    )
    assert support_response.status_code == 202
    async with api.sessions() as session:
        session.add(
            UserAchievement(
                user_id=api.current["principal"].user_id,
                achievement_key="first_break",
            )
        )
        await session.commit()
    redis = FakeLeaderboardRedis()
    api.app.state.redis = redis
    headers = {"Authorization": "Bearer test-access-token"}
    first = await api.client.request(
        "DELETE", "/v1/me", headers=headers, json={"confirmation": "DELETE"}
    )
    assert first.status_code == 503
    assert first.json()["code"] == "ACCOUNT_DELETION_PENDING"
    assert redis.version == 1
    async with api.sessions() as session:
        profile = await session.get(Profile, api.current["principal"].user_id)
        deletion = await session.scalar(select(AccountDeletionRequest))
        assert profile is not None and profile.deleted_at is not None
        assert profile.display_name is None and profile.public_leaderboards is False
        assert profile.is_anonymous is True
        assert deletion is not None and deletion.status == "provider_failed"
        challenge = await session.scalar(select(FriendChallenge))
        assert challenge is not None
        assert challenge.title is None and challenge.revoked_at is not None
        assert await session.scalar(select(func.count(SupportRequest.id))) == 0
        assert await session.scalar(select(func.count(UserAchievement.id))) == 0
    second = await api.client.request(
        "DELETE", "/v1/me", headers=headers, json={"confirmation": "DELETE"}
    )
    assert second.status_code == 200
    assert second.json() == {"deleted": True}
    third = await api.client.request(
        "DELETE", "/v1/me", headers=headers, json={"confirmation": "DELETE"}
    )
    assert third.status_code == 200
    assert provider.calls == 2
    assert provider.revocations == 2
    assert provider.events == ["revoke", "delete", "revoke", "delete"]
    async with api.sessions() as session:
        deletion = await session.scalar(select(AccountDeletionRequest))
        assert deletion is not None and deletion.status == "completed"


async def test_guest_export_and_account_deletion_require_upgrade(api: APIContext) -> None:
    api.current["principal"] = make_principal(anonymous=True)
    exported = await api.client.get("/v1/me/export")
    assert exported.status_code == 403
    assert exported.json()["code"] == "ACCOUNT_UPGRADE_REQUIRED"
    deleted = await api.client.request(
        "DELETE",
        "/v1/me",
        headers={"Authorization": "Bearer anonymous-access-token"},
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 403
    assert deleted.json()["code"] == "ACCOUNT_UPGRADE_REQUIRED"


async def test_account_deletion_requires_exact_confirmation_and_recent_auth(
    api: APIContext,
) -> None:
    missing = await api.client.delete("/v1/me")
    wrong = await api.client.request("DELETE", "/v1/me", json={"confirmation": "delete"})
    assert missing.status_code == 422
    assert wrong.status_code == 422

    current = api.current["principal"]
    api.current["principal"] = replace(
        current,
        authenticated_at=datetime.now(UTC) - timedelta(hours=1),
    )
    stale = await api.client.request(
        "DELETE",
        "/v1/me",
        headers={"Authorization": "Bearer stale-access-token"},
        json={"confirmation": "DELETE"},
    )
    assert stale.status_code == 401
    assert stale.json()["code"] == "RECENT_AUTH_REQUIRED"


async def test_daily_stats_use_challenge_date_and_expire_stale_streak(
    api: APIContext,
) -> None:
    started = await api.client.post("/v1/daily/start")
    assert started.status_code == 200, started.text
    old_day = datetime.now(UTC).date() - timedelta(days=5)
    async with api.sessions() as session:
        game = await session.scalar(
            select(GameSession).where(GameSession.public_id == started.json()["id"])
        )
        assert game is not None and game.daily_challenge_id is not None
        daily = await session.get(DailyChallenge, game.daily_challenge_id)
        assert daily is not None
        daily.challenge_date = old_day
        game.status = "lost"
        game.completed_at = datetime.now(UTC)
        await session.commit()

    stats = await api.client.get("/v1/me/stats")
    assert stats.status_code == 200, stats.text
    assert stats.json()["dailyCompletionHistory"] == [old_day.isoformat()]
    assert stats.json()["dailyStreak"] == 0
    assert stats.json()["achievementProgress"] == {"logic_week": {"current": 1, "target": 7}}


async def test_deletion_worker_completes_queued_provider_failure(api: APIContext) -> None:
    user_id = uuid.uuid4()
    async with api.sessions() as session:
        session.add(
            AccountDeletionRequest(
                user_id=user_id,
                status="provider_failed",
                provider_attempts=1,
                last_error_code="provider_unavailable",
            )
        )
        await session.commit()

    class AvailableProvider:
        def __init__(self) -> None:
            self.deleted: list[uuid.UUID] = []

        async def delete_user(self, target_id: uuid.UUID) -> None:
            self.deleted.append(target_id)

    provider = AvailableProvider()
    completed = await retry_pending_account_deletions(api.sessions, provider)  # type: ignore[arg-type]
    assert completed == 1
    assert provider.deleted == [user_id]
    async with api.sessions() as session:
        deletion = await session.scalar(
            select(AccountDeletionRequest).where(AccountDeletionRequest.user_id == user_id)
        )
        assert deletion is not None
        assert deletion.status == "completed"
        assert deletion.provider_attempts == 2
        assert deletion.last_error_code is None


async def test_admin_uses_database_grant_recent_auth_and_audits_mutation(api: APIContext) -> None:
    await api.client.get("/v1/me/profile")
    current_id = api.current["principal"].user_id
    api.current["principal"] = replace(make_principal(current_id), assurance_level="aal2")
    denied = await api.client.get("/v1/admin/summary")
    assert denied.status_code == 403
    async with api.sessions() as session:
        session.add(AdminGrant(user_id=api.current["principal"].user_id))
        await session.commit()
    api.current["principal"] = replace(
        make_principal(current_id, anonymous=True), assurance_level="aal2"
    )
    assert (await api.client.get("/v1/admin/summary")).status_code == 403
    api.current["principal"] = replace(
        make_principal(current_id), assurance_level="aal2", session_id=None
    )
    assert (await api.client.get("/v1/admin/summary")).status_code == 401
    api.current["principal"] = make_principal(current_id)
    mfa_denied = await api.client.get("/v1/admin/summary")
    assert mfa_denied.status_code == 401
    assert mfa_denied.json()["code"] == "MFA_REQUIRED"
    api.current["principal"] = type(api.current["principal"])(
        user_id=current_id,
        is_anonymous=False,
        session_id="old-session",
        issued_at=datetime.now(UTC) - timedelta(hours=1),
        authenticated_at=datetime.now(UTC) - timedelta(hours=1),
        assurance_level="aal2",
    )
    stale = await api.client.get("/v1/admin/summary")
    assert stale.status_code == 401
    assert stale.json()["code"] == "RECENT_AUTH_REQUIRED"
    api.current["principal"] = replace(make_principal(current_id), assurance_level="aal2")
    summary = await api.client.get("/v1/admin/summary")
    assert summary.status_code == 200, summary.text
    for route in ("games", "profiles", "rooms", "challenges", "leaderboard-review"):
        listing = await api.client.get(f"/v1/admin/{route}")
        assert listing.status_code == 200, listing.text
        assert {"items", "page", "pageSize", "total"}.issubset(listing.json())
    games = (await api.client.get("/v1/admin/games")).json()["items"]
    assert all("secret" not in game and "attempts" not in game for game in games)
    self_moderation = await api.client.post(
        f"/v1/admin/profiles/{current_id}/moderate",
        json={"reason": "Must require a second administrator", "enabled": True},
    )
    assert self_moderation.status_code == 409
    assert self_moderation.json()["code"] == "ADMIN_SELF_MODERATION_FORBIDDEN"
    changed = await api.client.patch(
        "/v1/admin/flags/daily", json={"reason": "Incident mitigation", "enabled": False}
    )
    assert changed.status_code == 200
    disabled = await api.client.get("/v1/daily")
    assert disabled.status_code == 503
    assert disabled.json()["code"] == "FEATURE_DISABLED"
    async with api.sessions() as session:
        flag = await session.get(FeatureFlag, "daily")
        audit = await session.scalar(
            select(AuditEvent).where(AuditEvent.action == "feature_flag.updated")
        )
        assert flag is not None and flag.enabled is False
        assert audit is not None and audit.actor_id == api.current["principal"].user_id


async def test_admin_moderation_refreshes_cached_leaderboard_privacy(
    api: APIContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    redis = FakeLeaderboardRedis()
    api.app.state.redis = redis
    api.app.state.redis_ready = True
    monkeypatch.setattr(services, "generate_secret", lambda _config: tuple("RBGY"))

    target = api.current["principal"]
    updated = await api.client.patch(
        "/v1/me/profile",
        json={"displayName": "Visible Player", "publicLeaderboards": True},
    )
    assert updated.status_code == 200, updated.text
    game = await api.client.post("/v1/games", json={"mode": "solo", "difficulty": "easy"})
    won = await api.client.post(
        f"/v1/games/{game.json()['id']}/attempts",
        json={"guess": list("RBGY"), "idempotencyKey": "moderation-win-00001"},
    )
    assert won.status_code == 200 and won.json()["status"] == "won"

    admin = replace(make_principal(), assurance_level="aal2")
    api.current["principal"] = admin
    assert (await api.client.get("/v1/me/profile")).status_code == 200
    async with api.sessions() as session:
        session.add(AdminGrant(user_id=admin.user_id))
        await session.commit()

    cached = await api.client.get("/v1/leaderboards")
    assert cached.status_code == 200, cached.text
    assert cached.json()["items"][0]["displayName"] == "Visible Player"

    prior_version = redis.version
    banned = await api.client.post(
        f"/v1/admin/profiles/{target.user_id}/moderate",
        json={"reason": "Confirmed leaderboard abuse", "enabled": True},
    )
    assert banned.status_code == 200, banned.text
    assert redis.version == prior_version + 1
    hidden = await api.client.get("/v1/leaderboards")
    assert hidden.json()["items"] == []

    prior_version = redis.version
    restored = await api.client.post(
        f"/v1/admin/profiles/{target.user_id}/moderate",
        json={
            "reason": "Appeal accepted after review",
            "enabled": False,
            "displayName": "Reviewed Player",
        },
    )
    assert restored.status_code == 200, restored.text
    assert redis.version == prior_version + 1
    refreshed = await api.client.get("/v1/leaderboards")
    assert refreshed.json()["items"][0]["displayName"] == "Reviewed Player"


async def test_support_request_is_validated_rate_limited_and_minimal(api: APIContext) -> None:
    invalid = await api.client.post(
        "/v1/support",
        json={"topic": "other", "replyEmail": "not-an-email", "message": "short"},
    )
    assert invalid.status_code == 422
    accepted = await api.client.post(
        "/v1/support",
        json={
            "topic": "accessibility",
            "replyEmail": "player@example.com",
            "message": "Keyboard focus disappears after I submit a row.",
        },
    )
    assert accepted.status_code == 202, accepted.text
    async with api.sessions() as session:
        support = await session.scalar(select(SupportRequest))
        assert support is not None
        assert support.user_id == api.current["principal"].user_id
        assert "ip" not in SupportRequest.__table__.columns
