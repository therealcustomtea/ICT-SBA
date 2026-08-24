# Documents the purpose or contract of this module, class, or function.
"""Create the Mastermind production schema.

Revision ID: 20260715_0001
Revises:
"""

# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Sequence

# Imports selected names from `typing` for use in this module.
from typing import Any

# Imports `sqlalchemy as sa` so the module can use that dependency.
import sqlalchemy as sa

# Imports selected names from `alembic` for use in this module.
from alembic import op

# Computes and stores `revision` for subsequent operations.
revision: str = "20260715_0001"
# Computes and stores `down_revision` for subsequent operations.
down_revision: str | None = None
# Computes and stores `branch_labels` for subsequent operations.
branch_labels: str | Sequence[str] | None = None
# Computes and stores `depends_on` for subsequent operations.
depends_on: str | Sequence[str] | None = None


# Defines the `timestamps` callable and its typed interface.
def timestamps() -> list[sa.Column[Any]]:
    # Returns this result to the caller and ends the current function.
    return [
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "created_at",
            # Defines the timezone-aware timestamp column type.
            sa.DateTime(timezone=True),
            # Uses the database clock when no timestamp is supplied.
            server_default=sa.func.now(),
            # Requires every stored row to contain this timestamp.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "updated_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    ]


# Defines the `upgrade` callable and its typed interface.
def upgrade() -> None:
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "profiles",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("display_name", sa.String(32)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("normalized_display_name", sa.String(32), unique=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("is_anonymous", sa.Boolean(), server_default=sa.true(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("public_leaderboards", sa.Boolean(), server_default=sa.false(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("is_banned", sa.Boolean(), server_default=sa.false(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        # Supplies this item to the surrounding call or collection.
        *timestamps(),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "daily_challenges",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("challenge_date", sa.Date(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("public_id", sa.String(40), nullable=False, unique=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("config", sa.JSON(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("derivation_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("derivation_key_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("rule_set_version", sa.String(32), nullable=False),
        # Supplies this item to the surrounding call or collection.
        *timestamps(),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("challenge_date", "rule_set_version"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "achievements",
        # Calls `sa.Column` with the supplied values.
        sa.Column("key", sa.String(40), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("name", sa.String(80), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("description", sa.String(200), nullable=False),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "feature_flags",
        # Calls `sa.Column` with the supplied values.
        sa.Column("key", sa.String(64), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("enabled", sa.Boolean(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("description", sa.String(200)),
        # Supplies this item to the surrounding call or collection.
        *timestamps(),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "admin_grants",
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "user_id",
            # Calls `sa.Uuid` with these supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with these supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `primary_key` value to the surrounding call.
            primary_key=True,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("granted_by", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "granted_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "friend_challenges",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("share_code_hash", sa.String(64), unique=True, nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("creation_idempotency_key", sa.String(80)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("creation_request_fingerprint", sa.String(64)),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "creator_id",
            # Calls `sa.Uuid` with the supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `nullable` parameter or keyword argument.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("title", sa.String(80)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("show_creator_name", sa.Boolean(), server_default=sa.true(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("config", sa.JSON(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("secret_nonce", sa.LargeBinary(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("secret_key_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Supplies this item to the surrounding call or collection.
        *timestamps(),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint(
            # Supplies this item to the surrounding call or collection.
            "creator_id",
            # Supplies this item to the surrounding call or collection.
            "creation_idempotency_key",
            # Provides the `name` parameter or keyword argument.
            name="uq_friend_challenge_creation_idempotency",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_index` with the supplied values.
    op.create_index(
        # Executes this statement as the next step in the surrounding logic.
        "ix_friend_challenges_creator_created",
        # Supplies this string to the surrounding call or collection.
        "friend_challenges",
        # Supplies this item to the surrounding call or collection.
        ["creator_id", "created_at"],
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "multiplayer_rooms",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("room_code_hash", sa.String(64), unique=True, nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("creation_idempotency_key", sa.String(80)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("creation_request_fingerprint", sa.String(64)),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "owner_id",
            # Calls `sa.Uuid` with these supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with these supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("config", sa.JSON(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("secret_nonce", sa.LargeBinary(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("secret_key_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("status", sa.String(24), server_default="waiting", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("winner_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        # Calls `sa.Column` with the supplied values.
        sa.Column("winner_at", sa.DateTime(timezone=True)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("tie_deadline", sa.DateTime(timezone=True)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("is_tie", sa.Boolean(), server_default=sa.false(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("event_sequence", sa.Integer(), server_default="0", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Supplies this item to the surrounding call or collection.
        *timestamps(),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "status IN ('waiting', 'active', 'completed', 'expired', 'terminated')",
            # Provides the `name` parameter or keyword argument.
            name="status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint("event_sequence >= 0", name="event_sequence_nonnegative"),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "owner_id",
            # Supplies this string to the surrounding call or collection.
            "creation_idempotency_key",
            # Provides the `name` value to the surrounding call.
            name="uq_room_creation_idempotency",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "game_sessions",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("public_id", sa.String(32), unique=True, nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("creation_idempotency_key", sa.String(80)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("creation_request_fingerprint", sa.String(64)),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "owner_id",
            # Calls `sa.Uuid` with these supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with these supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("mode", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("difficulty", sa.String(16)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("config", sa.JSON(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("status", sa.String(24), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("rule_set_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("scoring_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("secret_nonce", sa.LargeBinary(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("secret_key_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("attempts_used", sa.Integer(), server_default="0", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("maximum_attempts", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("elapsed_seconds", sa.Integer()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("final_score", sa.Integer()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("score_breakdown", sa.JSON()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("ranked_eligibility", sa.String(24), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("invalidation_reason", sa.String(200)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("invalid_submission_count", sa.Integer(), server_default="0", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "daily_challenge_id",
            # Calls `sa.Uuid` with the supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("daily_challenges.id", ondelete="RESTRICT"),
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "friend_challenge_id",
            # Calls `sa.Uuid` with the supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("friend_challenges.id", ondelete="SET NULL"),
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("room_id", sa.Uuid(), sa.ForeignKey("multiplayer_rooms.id", ondelete="SET NULL")),
        # Supplies this item to the surrounding call or collection.
        *timestamps(),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint("attempts_used >= 0", name="attempts_nonnegative"),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "attempts_used <= maximum_attempts",
            # Provides the `name` parameter or keyword argument.
            name="attempts_within_limit",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "maximum_attempts >= 1 AND maximum_attempts <= 20",
            # Provides the `name` parameter or keyword argument.
            name="attempt_limit",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "invalid_submission_count >= 0",
            # Provides the `name` parameter or keyword argument.
            name="invalid_submissions_nonnegative",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "mode IN ('solo', 'daily', 'practice', 'pass_and_play', 'friend_challenge', 'duel')",
            # Provides the `name` parameter or keyword argument.
            name="mode_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "status IN ('created', 'active', 'won', 'lost', 'abandoned', 'expired')",
            # Provides the `name` parameter or keyword argument.
            name="status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert')",
            # Provides the `name` parameter or keyword argument.
            name="difficulty_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "ranked_eligibility IN ('eligible', 'unranked', 'invalidated')",
            # Provides the `name` parameter or keyword argument.
            name="ranked_eligibility_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "elapsed_seconds IS NULL OR elapsed_seconds >= 0",
            # Provides the `name` parameter or keyword argument.
            name="elapsed_nonnegative",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "final_score IS NULL OR final_score >= 0",
            # Provides the `name` parameter or keyword argument.
            name="score_nonnegative",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "owner_id",
            # Supplies this string to the surrounding call or collection.
            "creation_idempotency_key",
            # Provides the `name` value to the surrounding call.
            name="uq_game_creation_idempotency",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("owner_id", "daily_challenge_id", name="uq_daily_official_run"),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("owner_id", "friend_challenge_id", name="uq_friend_official_run"),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("owner_id", "room_id", name="uq_room_member_game"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_index` with the supplied values.
    op.create_index("ix_game_sessions_owner_created", "game_sessions", ["owner_id", "created_at"])
    # Calls `op.create_index` with the supplied values.
    op.create_index("ix_game_sessions_status_mode", "game_sessions", ["status", "mode"])
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "game_attempts",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "game_id",
            # Calls `sa.Uuid` with the supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            # Provides the `nullable` parameter or keyword argument.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("guess", sa.JSON(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("black_pegs", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("white_pegs", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "submitted_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("idempotency_key", sa.String(80), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("request_id", sa.String(64), nullable=False),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint("black_pegs >= 0 AND white_pegs >= 0", name="feedback_nonnegative"),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "black_pegs + white_pegs <= json_array_length(guess)",
            # Provides the `name` parameter or keyword argument.
            name="feedback_within_code_length",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("game_id", "attempt_number", name="uq_game_attempt_number"),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("game_id", "idempotency_key", name="uq_game_attempt_idempotency"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "multiplayer_members",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "room_id",
            # Calls `sa.Uuid` with the supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"),
            # Provides the `nullable` parameter or keyword argument.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "user_id",
            # Calls `sa.Uuid` with these supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with these supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "joined_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "last_seen_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("connected", sa.Boolean(), server_default=sa.false(), nullable=False),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("room_id", "user_id"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "multiplayer_events",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "room_id",
            # Calls `sa.Uuid` with the supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"),
            # Provides the `nullable` parameter or keyword argument.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("sequence", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("event_type", sa.String(40), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("payload", sa.JSON(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "created_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("room_id", "sequence"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "leaderboard_entries",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "game_id",
            # Calls `sa.Uuid` with the supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            # Provides the `unique` parameter or keyword argument.
            unique=True,
            # Provides the `nullable` parameter or keyword argument.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "user_id",
            # Calls `sa.Uuid` with these supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with these supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("category", sa.String(48), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("score", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("attempts_used", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("elapsed_seconds", sa.Integer(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("review_status", sa.String(24), server_default="approved", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("invalidated_at", sa.DateTime(timezone=True)),
        # Supplies this item to the surrounding call or collection.
        *timestamps(),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint("score >= 0", name="score_nonnegative"),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "attempts_used >= 1 AND attempts_used <= 20",
            # Provides the `name` parameter or keyword argument.
            name="attempts_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint("elapsed_seconds >= 0", name="elapsed_nonnegative"),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "review_status IN ('approved', 'pending', 'invalidated', 'deleted_account')",
            # Provides the `name` parameter or keyword argument.
            name="review_status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_index` with the supplied values.
    op.create_index(
        # Supplies this item to the surrounding call or collection.
        "ix_leaderboard_rank",
        # Supplies this item to the surrounding call or collection.
        "leaderboard_entries",
        # Supplies this item to the surrounding call or collection.
        ["category", "score", "attempts_used", "elapsed_seconds"],
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "user_achievements",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "user_id",
            # Calls `sa.Uuid` with these supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with these supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "achievement_key",
            # Calls `sa.String` with the supplied values.
            sa.String(40),
            # Calls `sa.ForeignKey` with the supplied values.
            sa.ForeignKey("achievements.key", ondelete="CASCADE"),
            # Provides the `nullable` parameter or keyword argument.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "awarded_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("game_id", sa.Uuid(), sa.ForeignKey("game_sessions.id", ondelete="SET NULL")),
        # Calls `sa.UniqueConstraint` with the supplied values.
        sa.UniqueConstraint("user_id", "achievement_key"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "moderation_actions",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        # Calls `sa.Column` with the supplied values.
        sa.Column("target_user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        # Calls `sa.Column` with the supplied values.
        sa.Column("action", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("reason", sa.String(300), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "created_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "audit_events",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        # Calls `sa.Column` with the supplied values.
        sa.Column("action", sa.String(80), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("target_type", sa.String(40), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("target_id", sa.String(80), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("reason", sa.String(300)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("event_data", sa.JSON(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "created_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_index` with the supplied values.
    op.create_index("ix_audit_events_created", "audit_events", ["created_at"])
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "support_requests",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "user_id",
            # Calls `sa.Uuid` with these supplied values.
            sa.Uuid(),
            # Calls `sa.ForeignKey` with these supplied values.
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("topic", sa.String(40), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("reply_email", sa.String(254), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("message", sa.Text(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("status", sa.String(20), server_default="received", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "created_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_index` with the supplied values.
    op.create_index(
        # Executes this statement as the next step in the surrounding logic.
        "ix_support_requests_status_created",
        # Supplies this string to the surrounding call or collection.
        "support_requests",
        # Supplies this item to the surrounding call or collection.
        ["status", "created_at"],
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "account_deletion_requests",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("user_id", sa.Uuid(), unique=True, nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("status", sa.String(24), server_default="pending", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("provider_attempts", sa.Integer(), server_default="0", nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("last_error_code", sa.String(40)),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Supplies this item to the surrounding call or collection.
            "requested_at",
            # Calls `sa.DateTime` with the supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` parameter or keyword argument.
            server_default=sa.func.now(),
            # Provides the `nullable` parameter or keyword argument.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "status IN ('pending', 'provider_failed', 'completed')",
            # Provides the `name` parameter or keyword argument.
            name="status_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "provider_attempts >= 0",
            # Provides the `name` parameter or keyword argument.
            name="provider_attempts_nonnegative",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_table` with the supplied values.
    op.create_table(
        # Supplies this item to the surrounding call or collection.
        "product_events",
        # Calls `sa.Column` with the supplied values.
        sa.Column("id", sa.Uuid(), primary_key=True),
        # Calls `sa.Column` with the supplied values.
        sa.Column("client_event_id", sa.Uuid(), unique=True, nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("event_name", sa.String(40), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("anonymous", sa.Boolean(), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("consent_version", sa.String(32), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("release", sa.String(64), nullable=False),
        # Calls `sa.Column` with the supplied values.
        sa.Column("locale", sa.String(10)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("mode", sa.String(24)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("difficulty", sa.String(16)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("result", sa.String(16)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("attempts_used", sa.Integer()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("ranked", sa.Boolean()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("score_band", sa.String(16)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("daily_challenge_id", sa.String(64)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("official", sa.Boolean()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("expiry_band", sa.String(16)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("room_state", sa.String(16)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("reconnect", sa.Boolean()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("tie", sa.Boolean()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("validation_category", sa.String(24)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("surface", sa.String(16)),
        # Calls `sa.Column` with the supplied values.
        sa.Column("recovered", sa.Boolean()),
        # Calls `sa.Column` with the supplied values.
        sa.Column("previous_anonymous", sa.Boolean()),
        # Calls `sa.Column` with the supplied values.
        sa.Column(
            # Executes this statement as the next step in the surrounding logic.
            "occurred_at",
            # Calls `sa.DateTime` with these supplied values.
            sa.DateTime(timezone=True),
            # Provides the `server_default` value to the surrounding call.
            server_default=sa.func.now(),
            # Provides the `nullable` value to the surrounding call.
            nullable=False,
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.Column` with the supplied values.
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "event_name IN ('game_started', 'game_completed', 'game_abandoned', "
            # Executes this statement as the next step in the surrounding logic.
            "'difficulty_selected', 'daily_completed', 'friend_challenge_created', "
            # Executes this statement as the next step in the surrounding logic.
            "'room_joined', 'duel_completed', 'validation_error', 'reconnect', "
            # Supplies this item to the surrounding call or collection.
            "'account_upgraded')",
            # Provides the `name` parameter or keyword argument.
            name="event_name_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "locale IS NULL OR locale IN ('en', 'zh-Hant')",
            # Provides the `name` parameter or keyword argument.
            name="locale_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "mode IS NULL OR mode IN ('solo', 'daily', 'practice', 'pass_and_play', "
            # Supplies this item to the surrounding call or collection.
            "'friend_challenge', 'duel')",
            # Provides the `name` parameter or keyword argument.
            name="mode_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert', 'custom')",
            # Provides the `name` parameter or keyword argument.
            name="difficulty_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "result IS NULL OR result IN ('won', 'lost', 'abandoned', 'expired', 'tie')",
            # Provides the `name` parameter or keyword argument.
            name="result_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "attempts_used IS NULL OR attempts_used BETWEEN 0 AND 20",
            # Provides the `name` parameter or keyword argument.
            name="attempts_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "score_band IS NULL OR score_band IN ('zero', '1-999', '1000-1499', '1500+')",
            # Provides the `name` parameter or keyword argument.
            name="score_band_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "expiry_band IS NULL OR expiry_band = '30_days'",
            # Provides the `name` parameter or keyword argument.
            name="expiry_band_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "room_state IS NULL OR room_state IN "
            # Supplies this item to the surrounding call or collection.
            "('waiting', 'active', 'completed', 'expired', 'terminated')",
            # Provides the `name` parameter or keyword argument.
            name="room_state_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Executes this statement as the next step in the surrounding logic.
            "validation_category IS NULL OR validation_category IN "
            # Supplies this item to the surrounding call or collection.
            "('game_config', 'guess', 'challenge', 'room', 'profile', 'auth')",
            # Provides the `name` parameter or keyword argument.
            name="validation_category_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint(
            # Supplies this item to the surrounding call or collection.
            "surface IS NULL OR surface IN ('game', 'room', 'daily', 'challenge', 'account')",
            # Provides the `name` parameter or keyword argument.
            name="surface_allowed",
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Calls `sa.CheckConstraint` with the supplied values.
        sa.CheckConstraint("expires_at > occurred_at", name="expiry_after_occurrence"),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_index` with the supplied values.
    op.create_index(
        # Executes this statement as the next step in the surrounding logic.
        "ix_product_events_event_occurred",
        # Supplies this string to the surrounding call or collection.
        "product_events",
        # Supplies this item to the surrounding call or collection.
        ["event_name", "occurred_at"],
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.create_index` with the supplied values.
    op.create_index("ix_product_events_expires", "product_events", ["expires_at"])

    # Computes and stores `achievement_rows` for subsequent operations.
    achievement_rows = [
        # Supplies this item to the surrounding call or collection.
        ("first_break", "First Break", "Win your first game."),
        # Supplies this item to the surrounding call or collection.
        ("one_shot", "One Shot", "Solve a code on your first attempt."),
        # Supplies this item to the surrounding call or collection.
        ("no_waste", "No Waste", "Win without an invalid submission."),
        # Supplies this item to the surrounding call or collection.
        ("daily_debut", "Daily Debut", "Complete your first daily challenge."),
        # Supplies this item to the surrounding call or collection.
        ("logic_week", "Logic Week", "Complete seven daily challenges."),
        # Supplies this item to the surrounding call or collection.
        ("hard_mode", "Hard Mode", "Win an official Hard game."),
        # Supplies this item to the surrounding call or collection.
        ("expert_breaker", "Expert Breaker", "Win an official Expert game."),
        # Supplies this item to the surrounding call or collection.
        ("challenger", "Challenger", "Complete a friend challenge."),
        # Supplies this item to the surrounding call or collection.
        ("duelist", "Duelist", "Win a private real-time duel."),
        # Closes the multiline call, declaration, or collection started above.
    ]
    # Computes and stores `achievement_table` for subsequent operations.
    achievement_table = sa.table(
        # Supplies this item to the surrounding call or collection.
        "achievements",
        # Calls `sa.column` with the supplied values.
        sa.column("key", sa.String()),
        # Calls `sa.column` with the supplied values.
        sa.column("version", sa.Integer()),
        # Calls `sa.column` with the supplied values.
        sa.column("name", sa.String()),
        # Calls `sa.column` with the supplied values.
        sa.column("description", sa.String()),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.bulk_insert` with the supplied values.
    op.bulk_insert(
        # Supplies this item to the surrounding call or collection.
        achievement_table,
        # Begins the nested block or multiline expression completed below.
        [
            # Executes this statement as the next step in the surrounding logic.
            {"key": key, "version": 1, "name": name, "description": description}
            # Iterates through the supplied values for the nested operation.
            for key, name, description in achievement_rows
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Closes the multiline call, declaration, or collection started above.
    )
    # Computes and stores `flag_table` for subsequent operations.
    flag_table = sa.table(
        # Supplies this item to the surrounding call or collection.
        "feature_flags",
        # Calls `sa.column` with the supplied values.
        sa.column("key", sa.String()),
        # Calls `sa.column` with the supplied values.
        sa.column("enabled", sa.Boolean()),
        # Calls `sa.column` with the supplied values.
        sa.column("description", sa.String()),
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.bulk_insert` with the supplied values.
    op.bulk_insert(
        # Supplies this item to the surrounding call or collection.
        flag_table,
        # Begins the nested block or multiline expression completed below.
        [
            # Executes this statement as the next step in the surrounding logic.
            {"key": key, "enabled": True, "description": description}
            # Iterates through the supplied values for the nested operation.
            for key, description in (
                # Supplies this item to the surrounding call or collection.
                ("daily", "Official daily challenge"),
                # Supplies this item to the surrounding call or collection.
                ("leaderboards", "Public leaderboards"),
                # Supplies this item to the surrounding call or collection.
                ("friend_challenges", "Private asynchronous challenges"),
                # Supplies this item to the surrounding call or collection.
                ("multiplayer", "Private real-time duels"),
                # Supplies this item to the surrounding call or collection.
                ("achievements", "Achievement awarding"),
                # Supplies this item to the surrounding call or collection.
                ("account_registration", "Registered account upgrades"),
                # Supplies this item to the surrounding call or collection.
                ("analytics", "Privacy-conscious first-party analytics"),
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Closes the multiline call, declaration, or collection started above.
    )

    # Checks this condition before executing the nested branch.
    if op.get_bind().dialect.name == "postgresql":
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Documents the purpose or contract of this module, class, or function.
            """
            DO $$ BEGIN
              CREATE ROLE mastermind_runtime NOLOGIN;
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$
            """
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `table_privileges` for subsequent operations.
        table_privileges = {
            # Associates the `profiles` key with its value.
            "profiles": "SELECT, INSERT, UPDATE",
            # Associates the `daily_challenges` key with its value.
            "daily_challenges": "SELECT, INSERT",
            # Associates the `friend_challenges` key with its value.
            "friend_challenges": "SELECT, INSERT, UPDATE",
            # Associates the `multiplayer_rooms` key with its value.
            "multiplayer_rooms": "SELECT, INSERT, UPDATE",
            # Associates the `game_sessions` key with its value.
            "game_sessions": "SELECT, INSERT, UPDATE",
            # Associates the `game_attempts` key with its value.
            "game_attempts": "SELECT, INSERT",
            # Associates the `multiplayer_members` key with its value.
            "multiplayer_members": "SELECT, INSERT, UPDATE",
            # Associates the `multiplayer_events` key with its value.
            "multiplayer_events": "SELECT, INSERT",
            # Associates the `leaderboard_entries` key with its value.
            "leaderboard_entries": "SELECT, INSERT, UPDATE",
            # Associates the `achievements` key with its value.
            "achievements": "SELECT",
            # Associates the `user_achievements` key with its value.
            "user_achievements": "SELECT, INSERT, DELETE",
            # Associates the `feature_flags` key with its value.
            "feature_flags": "SELECT, UPDATE",
            # Associates the `moderation_actions` key with its value.
            "moderation_actions": "INSERT",
            # Associates the `audit_events` key with its value.
            "audit_events": "SELECT, INSERT",
            # Associates the `admin_grants` key with its value.
            "admin_grants": "SELECT, DELETE",
            # Associates the `support_requests` key with its value.
            "support_requests": "INSERT, DELETE",
            # Associates the `account_deletion_requests` key with its value.
            "account_deletion_requests": "SELECT, INSERT, UPDATE",
            # Closes the multiline call, declaration, or collection started above.
        }
        # Iterates through the supplied values for the nested operation.
        for table, privileges in table_privileges.items():
            # Calls `op.execute` with the supplied values.
            op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
            # Calls `op.execute` with the supplied values.
            op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC")
            # Calls `op.execute` with the supplied values.
            op.execute(
                # Executes this statement as the next step in the surrounding logic.
                f"""
                DO $$ BEGIN
                  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                    REVOKE ALL ON TABLE public.{table} FROM anon;
                  END IF;
                  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                    REVOKE ALL ON TABLE public.{table} FROM authenticated;
                  END IF;
                END $$
                """
                # Closes the multiline call, declaration, or collection started above.
            )
            # Calls `op.execute` with the supplied values.
            op.execute(f"GRANT {privileges} ON TABLE public.{table} TO mastermind_runtime")
            # Calls `op.execute` with the supplied values.
            op.execute(
                # Executes this statement as the next step in the surrounding logic.
                f"""
                CREATE POLICY mastermind_runtime_all ON public.{table}
                FOR ALL TO mastermind_runtime USING (true) WITH CHECK (true)
                """
                # Closes the multiline call, declaration, or collection started above.
            )
        # Calls `op.execute` with the supplied values.
        op.execute("ALTER TABLE public.product_events ENABLE ROW LEVEL SECURITY")
        # Calls `op.execute` with the supplied values.
        op.execute("REVOKE ALL ON TABLE public.product_events FROM PUBLIC")
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Documents the purpose or contract of this module, class, or function.
            """
            DO $$ BEGIN
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                REVOKE ALL ON TABLE public.product_events FROM anon;
              END IF;
              IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                REVOKE ALL ON TABLE public.product_events FROM authenticated;
              END IF;
            END $$
            """
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `op.execute` with the supplied values.
        op.execute("GRANT INSERT ON TABLE public.product_events TO mastermind_runtime")
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Documents the purpose or contract of this module, class, or function.
            """
            CREATE POLICY mastermind_runtime_insert ON public.product_events
            FOR INSERT TO mastermind_runtime WITH CHECK (true)
            """
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `op.execute` with the supplied values.
        op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC")
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Executes this statement as the next step in the surrounding logic.
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
            # Closes the multiline call, declaration, or collection started above.
        )


# Defines the `downgrade` callable and its typed interface.
def downgrade() -> None:
    # Iterates through the supplied values for the nested operation.
    for table in [
        # Supplies this item to the surrounding call or collection.
        "product_events",
        # Supplies this item to the surrounding call or collection.
        "support_requests",
        # Supplies this item to the surrounding call or collection.
        "account_deletion_requests",
        # Supplies this item to the surrounding call or collection.
        "audit_events",
        # Supplies this item to the surrounding call or collection.
        "moderation_actions",
        # Supplies this item to the surrounding call or collection.
        "user_achievements",
        # Supplies this item to the surrounding call or collection.
        "leaderboard_entries",
        # Supplies this item to the surrounding call or collection.
        "multiplayer_events",
        # Supplies this item to the surrounding call or collection.
        "multiplayer_members",
        # Supplies this item to the surrounding call or collection.
        "game_attempts",
        # Supplies this item to the surrounding call or collection.
        "game_sessions",
        # Supplies this item to the surrounding call or collection.
        "multiplayer_rooms",
        # Supplies this item to the surrounding call or collection.
        "friend_challenges",
        # Supplies this item to the surrounding call or collection.
        "admin_grants",
        # Supplies this item to the surrounding call or collection.
        "feature_flags",
        # Supplies this item to the surrounding call or collection.
        "achievements",
        # Supplies this item to the surrounding call or collection.
        "daily_challenges",
        # Supplies this item to the surrounding call or collection.
        "profiles",
        # Begins the nested block or multiline expression completed below.
    ]:
        # Calls `op.drop_table` with the supplied values.
        op.drop_table(table)
