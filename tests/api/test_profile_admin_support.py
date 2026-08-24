# Defers annotation evaluation so modern type hints remain safe at runtime.
from __future__ import annotations

# Imports `io` because this module uses that dependency.
import io

# Imports `uuid` because this module uses that dependency.
import uuid

# Imports `zipfile` because this module uses that dependency.
import zipfile

# Imports the required names from `datetime` for this module.
from datetime import UTC, datetime

# Imports the required names from `mastermind_api.auth` for this module.
from mastermind_api.auth import AuthPrincipal

# Imports the required names from `mastermind_api.models` for this module.
from mastermind_api.models import (
    # Supplies this required nested value.
    AdminGrant,
    # Supplies this required nested value.
    AuditEvent,
    # Supplies this required nested value.
    AuthUser,
    # Supplies this required nested value.
    Profile,
    # Supplies this required nested value.
    SupportRequest,
    # Closes the multiline declaration, call, or collection opened above.
)

# Imports the required names from `.conftest` for this module.
from .conftest import APIContext, principal


# Defines this callable to implement the operation described by its name.
def pass_and_play_payload() -> dict[str, object]:
    # Returns the computed result and ends the current callable.
    return {
        # Supplies this literal value to the surrounding declaration or call.
        "mode": "pass_and_play",
        # Supplies this literal value to the surrounding declaration or call.
        "codeMaker": "human",
        # Supplies this literal value to the surrounding declaration or call.
        "secret": ["R", "B", "G", "Y"],
        # Supplies this literal value to the surrounding declaration or call.
        "config": {
            # Supplies this literal value to the surrounding declaration or call.
            "codeLength": 4,
            # Supplies this literal value to the surrounding declaration or call.
            "colors": ["R", "B", "G", "Y", "O", "P"],
            # Supplies this literal value to the surrounding declaration or call.
            "allowDuplicates": True,
            # Supplies this literal value to the surrounding declaration or call.
            "maximumAttempts": 10,
            # Closes the multiline declaration, call, or collection opened above.
        },
        # Closes the multiline declaration, call, or collection opened above.
    }


# Defines this callable to implement the operation described by its name.
async def test_profile_stats_and_archive_export(api: APIContext) -> None:
    # Stores `created` because later steps depend on this value.
    created = await api.client.post("/v1/games", json=pass_and_play_payload())
    # Stores `won` because later steps depend on this value.
    won = await api.client.post(
        # Supplies this required nested value.
        f"/v1/games/{created.json()['id']}/attempts",
        # Stores `json` because later steps depend on this value.
        json={"guess": ["R", "B", "G", "Y"], "idempotencyKey": "profile-win-001"},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert won.status_code == 200
    # Stores `stats` because later steps depend on this value.
    stats = await api.client.get("/v1/me/stats")
    # Performs this required operation before the surrounding flow continues.
    assert stats.status_code == 200
    # Performs this required operation before the surrounding flow continues.
    assert stats.json()["gamesWon"] == 1

    # Stores `registered` because later steps depend on this value.
    registered = principal(api.current["principal"].user_id)
    # Supplies this required nested value.
    api.current["principal"] = registered
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Stores `profile` because later steps depend on this value.
        profile = await session.get(Profile, registered.user_id)
        # Performs this required operation before the surrounding flow continues.
        assert profile is not None
        # Stores `profile.is_anonymous` because later steps depend on this value.
        profile.is_anonymous = False
        # Supplies this required nested value.
        session.add(
            # Supplies this required nested value.
            AuthUser(
                # Stores `id` because later steps depend on this value.
                id=registered.user_id,
                # Stores `email` because later steps depend on this value.
                email="player@example.com",
                # Stores `normalized_email` because later steps depend on this value.
                normalized_email="player@example.com",
                # Stores `is_anonymous` because later steps depend on this value.
                is_anonymous=False,
                # Stores `email_verified_at` because later steps depend on this value.
                email_verified_at=datetime.now(UTC),
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Performs this required operation before the surrounding flow continues.
        await session.commit()
    # Stores `exported` because later steps depend on this value.
    exported = await api.client.get("/v1/me/export")
    # Performs this required operation before the surrounding flow continues.
    assert exported.status_code == 200
    # Scopes this resource so acquisition and cleanup remain paired.
    with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
        # Performs this required operation before the surrounding flow continues.
        assert {"profile.json", "games.json", "attempts.json"} <= set(archive.namelist())


# Defines this callable to implement the operation described by its name.
async def test_first_party_account_deletion_revokes_identity_and_erases_profile(
    # Declares this typed field so the surrounding contract is explicit.
    api: APIContext,
    # Closes the multiline declaration, call, or collection opened above.
) -> None:
    # Stores `registered` because later steps depend on this value.
    registered = principal(anonymous=False)
    # Supplies this required nested value.
    api.current["principal"] = registered
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Supplies this required nested value.
        session.add(
            # Supplies this required nested value.
            AuthUser(
                # Stores `id` because later steps depend on this value.
                id=registered.user_id,
                # Stores `email` because later steps depend on this value.
                email="delete@example.com",
                # Stores `normalized_email` because later steps depend on this value.
                normalized_email="delete@example.com",
                # Stores `is_anonymous` because later steps depend on this value.
                is_anonymous=False,
                # Stores `email_verified_at` because later steps depend on this value.
                email_verified_at=datetime.now(UTC),
                # Closes the multiline declaration, call, or collection opened above.
            )
            # Closes the multiline declaration, call, or collection opened above.
        )
        # Supplies this required nested value.
        session.add(Profile(id=registered.user_id, is_anonymous=False, display_name="Delete Me"))
        # Performs this required operation before the surrounding flow continues.
        await session.commit()
    # Stores `deleted` because later steps depend on this value.
    deleted = await api.client.request("DELETE", "/v1/me", json={"confirmation": "DELETE"})
    # Performs this required operation before the surrounding flow continues.
    assert deleted.status_code == 200, deleted.text
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Stores `user` because later steps depend on this value.
        user = await session.get(AuthUser, registered.user_id)
        # Stores `profile` because later steps depend on this value.
        profile = await session.get(Profile, registered.user_id)
        # Performs this required operation before the surrounding flow continues.
        assert user is not None and user.email is None and user.deleted_at is not None
        # Performs this required operation before the surrounding flow continues.
        assert profile is not None and profile.deleted_at is not None


# Defines this callable to implement the operation described by its name.
async def test_admin_database_grant_and_audit_mutation(api: APIContext) -> None:
    # Stores `admin` because later steps depend on this value.
    admin = AuthPrincipal(
        # Stores `user_id` because later steps depend on this value.
        user_id=uuid.uuid4(),
        # Stores `is_anonymous` because later steps depend on this value.
        is_anonymous=False,
        # Stores `session_id` because later steps depend on this value.
        session_id=str(uuid.uuid4()),
        # Stores `issued_at` because later steps depend on this value.
        issued_at=datetime.now(UTC),
        # Stores `authenticated_at` because later steps depend on this value.
        authenticated_at=datetime.now(UTC),
        # Stores `assurance_level` because later steps depend on this value.
        assurance_level="aal2",
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Supplies this required nested value.
    api.current["principal"] = admin
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Supplies this required nested value.
        session.add(Profile(id=admin.user_id, is_anonymous=False))
        # Supplies this required nested value.
        session.add(AdminGrant(user_id=admin.user_id))
        # Performs this required operation before the surrounding flow continues.
        await session.commit()
    # Stores `response` because later steps depend on this value.
    response = await api.client.patch(
        # Supplies this literal value to the surrounding declaration or call.
        "/v1/admin/flags/daily",
        json={"reason": "Scheduled maintenance", "enabled": False},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert response.status_code == 200, response.text
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Stores `event` because later steps depend on this value.
        event = await session.find_one(AuditEvent, {"action": "feature_flag.updated"})
        # Performs this required operation before the surrounding flow continues.
        assert event is not None and event.actor_id == admin.user_id


# Defines this callable to implement the operation described by its name.
async def test_support_request_is_validated_and_persisted(api: APIContext) -> None:
    # Stores `invalid` because later steps depend on this value.
    invalid = await api.client.post(
        # Supplies this literal value to the surrounding declaration or call.
        "/v1/support",
        # Stores `json` because later steps depend on this value.
        json={"topic": "other", "replyEmail": "not-an-email", "message": "short"},
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert invalid.status_code == 422
    # Stores `accepted` because later steps depend on this value.
    accepted = await api.client.post(
        # Supplies this literal value to the surrounding declaration or call.
        "/v1/support",
        # Stores `json` because later steps depend on this value.
        json={
            # Supplies this literal value to the surrounding declaration or call.
            "topic": "accessibility",
            # Supplies this literal value to the surrounding declaration or call.
            "replyEmail": "player@example.com",
            # Supplies this literal value to the surrounding declaration or call.
            "message": "Keyboard focus is difficult to follow.",
            # Closes the multiline declaration, call, or collection opened above.
        },
        # Closes the multiline declaration, call, or collection opened above.
    )
    # Performs this required operation before the surrounding flow continues.
    assert accepted.status_code == 202
    # Scopes this resource so acquisition and cleanup remain paired.
    async with api.sessions() as session:
        # Stores `request` because later steps depend on this value.
        request = await session.find_one(SupportRequest, {"_id": uuid.UUID(accepted.json()["id"])})
        # Performs this required operation before the surrounding flow continues.
        assert request is not None and request.reply_email == "player@example.com"
