"""Create the Mastermind production schema.

Revision ID: 20260715_0001
Revises:
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op

revision: str = "20260715_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column[Any]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("display_name", sa.String(32)),
        sa.Column("normalized_display_name", sa.String(32), unique=True),
        sa.Column("is_anonymous", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("public_leaderboards", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_banned", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        *timestamps(),
    )
    op.create_table(
        "daily_challenges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("challenge_date", sa.Date(), nullable=False),
        sa.Column("public_id", sa.String(40), nullable=False, unique=True),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("derivation_version", sa.String(32), nullable=False),
        sa.Column("derivation_key_version", sa.String(32), nullable=False),
        sa.Column("rule_set_version", sa.String(32), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("challenge_date", "rule_set_version"),
    )
    op.create_table(
        "achievements",
        sa.Column("key", sa.String(40), primary_key=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
    )
    op.create_table(
        "feature_flags",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("description", sa.String(200)),
        *timestamps(),
    )
    op.create_table(
        "admin_grants",
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("granted_by", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column(
            "granted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "friend_challenges",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("share_code_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("creation_idempotency_key", sa.String(80)),
        sa.Column("creation_request_fingerprint", sa.String(64)),
        sa.Column(
            "creator_id",
            sa.Uuid(),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(80)),
        sa.Column("show_creator_name", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=False),
        sa.Column("secret_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("secret_key_version", sa.String(32), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.UniqueConstraint(
            "creator_id",
            "creation_idempotency_key",
            name="uq_friend_challenge_creation_idempotency",
        ),
    )
    op.create_index(
        "ix_friend_challenges_creator_created", "friend_challenges", ["creator_id", "created_at"]
    )
    op.create_table(
        "multiplayer_rooms",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("room_code_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("creation_idempotency_key", sa.String(80)),
        sa.Column("creation_request_fingerprint", sa.String(64)),
        sa.Column(
            "owner_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=False),
        sa.Column("secret_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("secret_key_version", sa.String(32), nullable=False),
        sa.Column("status", sa.String(24), server_default="waiting", nullable=False),
        sa.Column("winner_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("winner_at", sa.DateTime(timezone=True)),
        sa.Column("tie_deadline", sa.DateTime(timezone=True)),
        sa.Column("is_tie", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("event_sequence", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        *timestamps(),
        sa.CheckConstraint(
            "status IN ('waiting', 'active', 'completed', 'expired', 'terminated')",
            name="status_allowed",
        ),
        sa.CheckConstraint("event_sequence >= 0", name="event_sequence_nonnegative"),
        sa.UniqueConstraint(
            "owner_id", "creation_idempotency_key", name="uq_room_creation_idempotency"
        ),
    )
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("public_id", sa.String(32), unique=True, nullable=False),
        sa.Column("creation_idempotency_key", sa.String(80)),
        sa.Column("creation_request_fingerprint", sa.String(64)),
        sa.Column(
            "owner_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("difficulty", sa.String(16)),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("rule_set_version", sa.String(32), nullable=False),
        sa.Column("scoring_version", sa.String(32), nullable=False),
        sa.Column("encrypted_secret", sa.LargeBinary(), nullable=False),
        sa.Column("secret_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("secret_key_version", sa.String(32), nullable=False),
        sa.Column("attempts_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("maximum_attempts", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("elapsed_seconds", sa.Integer()),
        sa.Column("final_score", sa.Integer()),
        sa.Column("score_breakdown", sa.JSON()),
        sa.Column("ranked_eligibility", sa.String(24), nullable=False),
        sa.Column("invalidation_reason", sa.String(200)),
        sa.Column("invalid_submission_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "daily_challenge_id",
            sa.Uuid(),
            sa.ForeignKey("daily_challenges.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "friend_challenge_id",
            sa.Uuid(),
            sa.ForeignKey("friend_challenges.id", ondelete="SET NULL"),
        ),
        sa.Column("room_id", sa.Uuid(), sa.ForeignKey("multiplayer_rooms.id", ondelete="SET NULL")),
        *timestamps(),
        sa.CheckConstraint("attempts_used >= 0", name="attempts_nonnegative"),
        sa.CheckConstraint(
            "attempts_used <= maximum_attempts",
            name="attempts_within_limit",
        ),
        sa.CheckConstraint(
            "maximum_attempts >= 1 AND maximum_attempts <= 20",
            name="attempt_limit",
        ),
        sa.CheckConstraint(
            "invalid_submission_count >= 0",
            name="invalid_submissions_nonnegative",
        ),
        sa.CheckConstraint(
            "mode IN ('solo', 'daily', 'practice', 'pass_and_play', 'friend_challenge', 'duel')",
            name="mode_allowed",
        ),
        sa.CheckConstraint(
            "status IN ('created', 'active', 'won', 'lost', 'abandoned', 'expired')",
            name="status_allowed",
        ),
        sa.CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert')",
            name="difficulty_allowed",
        ),
        sa.CheckConstraint(
            "ranked_eligibility IN ('eligible', 'unranked', 'invalidated')",
            name="ranked_eligibility_allowed",
        ),
        sa.CheckConstraint(
            "elapsed_seconds IS NULL OR elapsed_seconds >= 0",
            name="elapsed_nonnegative",
        ),
        sa.CheckConstraint(
            "final_score IS NULL OR final_score >= 0",
            name="score_nonnegative",
        ),
        sa.UniqueConstraint(
            "owner_id", "creation_idempotency_key", name="uq_game_creation_idempotency"
        ),
        sa.UniqueConstraint("owner_id", "daily_challenge_id", name="uq_daily_official_run"),
        sa.UniqueConstraint("owner_id", "friend_challenge_id", name="uq_friend_official_run"),
        sa.UniqueConstraint("owner_id", "room_id", name="uq_room_member_game"),
    )
    op.create_index("ix_game_sessions_owner_created", "game_sessions", ["owner_id", "created_at"])
    op.create_index("ix_game_sessions_status_mode", "game_sessions", ["status", "mode"])
    op.create_table(
        "game_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "game_id",
            sa.Uuid(),
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("guess", sa.JSON(), nullable=False),
        sa.Column("black_pegs", sa.Integer(), nullable=False),
        sa.Column("white_pegs", sa.Integer(), nullable=False),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("idempotency_key", sa.String(80), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.CheckConstraint("attempt_number >= 1", name="attempt_number_positive"),
        sa.CheckConstraint("black_pegs >= 0 AND white_pegs >= 0", name="feedback_nonnegative"),
        sa.CheckConstraint(
            "black_pegs + white_pegs <= json_array_length(guess)",
            name="feedback_within_code_length",
        ),
        sa.UniqueConstraint("game_id", "attempt_number", name="uq_game_attempt_number"),
        sa.UniqueConstraint("game_id", "idempotency_key", name="uq_game_attempt_idempotency"),
    )
    op.create_table(
        "multiplayer_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "room_id",
            sa.Uuid(),
            sa.ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("connected", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.UniqueConstraint("room_id", "user_id"),
    )
    op.create_table(
        "multiplayer_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "room_id",
            sa.Uuid(),
            sa.ForeignKey("multiplayer_rooms.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("room_id", "sequence"),
    )
    op.create_table(
        "leaderboard_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "game_id",
            sa.Uuid(),
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
        ),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("category", sa.String(48), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("attempts_used", sa.Integer(), nullable=False),
        sa.Column("elapsed_seconds", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_status", sa.String(24), server_default="approved", nullable=False),
        sa.Column("invalidated_at", sa.DateTime(timezone=True)),
        *timestamps(),
        sa.CheckConstraint("score >= 0", name="score_nonnegative"),
        sa.CheckConstraint(
            "attempts_used >= 1 AND attempts_used <= 20",
            name="attempts_allowed",
        ),
        sa.CheckConstraint("elapsed_seconds >= 0", name="elapsed_nonnegative"),
        sa.CheckConstraint(
            "review_status IN ('approved', 'pending', 'invalidated', 'deleted_account')",
            name="review_status_allowed",
        ),
    )
    op.create_index(
        "ix_leaderboard_rank",
        "leaderboard_entries",
        ["category", "score", "attempts_used", "elapsed_seconds"],
    )
    op.create_table(
        "user_achievements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "achievement_key",
            sa.String(40),
            sa.ForeignKey("achievements.key", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "awarded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("game_id", sa.Uuid(), sa.ForeignKey("game_sessions.id", ondelete="SET NULL")),
        sa.UniqueConstraint("user_id", "achievement_key"),
    )
    op.create_table(
        "moderation_actions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("target_user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(300), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("target_id", sa.String(80), nullable=False),
        sa.Column("reason", sa.String(300)),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_audit_events_created", "audit_events", ["created_at"])
    op.create_table(
        "support_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("topic", sa.String(40), nullable=False),
        sa.Column("reply_email", sa.String(254), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="received", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_support_requests_status_created", "support_requests", ["status", "created_at"]
    )
    op.create_table(
        "account_deletion_requests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), unique=True, nullable=False),
        sa.Column("status", sa.String(24), server_default="pending", nullable=False),
        sa.Column("provider_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error_code", sa.String(40)),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('pending', 'provider_failed', 'completed')",
            name="status_allowed",
        ),
        sa.CheckConstraint(
            "provider_attempts >= 0",
            name="provider_attempts_nonnegative",
        ),
    )
    op.create_table(
        "product_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("client_event_id", sa.Uuid(), unique=True, nullable=False),
        sa.Column("event_name", sa.String(40), nullable=False),
        sa.Column("anonymous", sa.Boolean(), nullable=False),
        sa.Column("consent_version", sa.String(32), nullable=False),
        sa.Column("release", sa.String(64), nullable=False),
        sa.Column("locale", sa.String(10)),
        sa.Column("mode", sa.String(24)),
        sa.Column("difficulty", sa.String(16)),
        sa.Column("result", sa.String(16)),
        sa.Column("attempts_used", sa.Integer()),
        sa.Column("ranked", sa.Boolean()),
        sa.Column("score_band", sa.String(16)),
        sa.Column("daily_challenge_id", sa.String(64)),
        sa.Column("official", sa.Boolean()),
        sa.Column("expiry_band", sa.String(16)),
        sa.Column("room_state", sa.String(16)),
        sa.Column("reconnect", sa.Boolean()),
        sa.Column("tie", sa.Boolean()),
        sa.Column("validation_category", sa.String(24)),
        sa.Column("surface", sa.String(16)),
        sa.Column("recovered", sa.Boolean()),
        sa.Column("previous_anonymous", sa.Boolean()),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "event_name IN ('game_started', 'game_completed', 'game_abandoned', "
            "'difficulty_selected', 'daily_completed', 'friend_challenge_created', "
            "'room_joined', 'duel_completed', 'validation_error', 'reconnect', "
            "'account_upgraded')",
            name="event_name_allowed",
        ),
        sa.CheckConstraint(
            "locale IS NULL OR locale IN ('en', 'zh-Hant')",
            name="locale_allowed",
        ),
        sa.CheckConstraint(
            "mode IS NULL OR mode IN ('solo', 'daily', 'practice', 'pass_and_play', "
            "'friend_challenge', 'duel')",
            name="mode_allowed",
        ),
        sa.CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('easy', 'normal', 'hard', 'expert', 'custom')",
            name="difficulty_allowed",
        ),
        sa.CheckConstraint(
            "result IS NULL OR result IN ('won', 'lost', 'abandoned', 'expired', 'tie')",
            name="result_allowed",
        ),
        sa.CheckConstraint(
            "attempts_used IS NULL OR attempts_used BETWEEN 0 AND 20",
            name="attempts_allowed",
        ),
        sa.CheckConstraint(
            "score_band IS NULL OR score_band IN ('zero', '1-999', '1000-1499', '1500+')",
            name="score_band_allowed",
        ),
        sa.CheckConstraint(
            "expiry_band IS NULL OR expiry_band = '30_days'",
            name="expiry_band_allowed",
        ),
        sa.CheckConstraint(
            "room_state IS NULL OR room_state IN "
            "('waiting', 'active', 'completed', 'expired', 'terminated')",
            name="room_state_allowed",
        ),
        sa.CheckConstraint(
            "validation_category IS NULL OR validation_category IN "
            "('game_config', 'guess', 'challenge', 'room', 'profile', 'auth')",
            name="validation_category_allowed",
        ),
        sa.CheckConstraint(
            "surface IS NULL OR surface IN ('game', 'room', 'daily', 'challenge', 'account')",
            name="surface_allowed",
        ),
        sa.CheckConstraint("expires_at > occurred_at", name="expiry_after_occurrence"),
    )
    op.create_index(
        "ix_product_events_event_occurred", "product_events", ["event_name", "occurred_at"]
    )
    op.create_index("ix_product_events_expires", "product_events", ["expires_at"])

    achievement_rows = [
        ("first_break", "First Break", "Win your first game."),
        ("one_shot", "One Shot", "Solve a code on your first attempt."),
        ("no_waste", "No Waste", "Win without an invalid submission."),
        ("daily_debut", "Daily Debut", "Complete your first daily challenge."),
        ("logic_week", "Logic Week", "Complete seven daily challenges."),
        ("hard_mode", "Hard Mode", "Win an official Hard game."),
        ("expert_breaker", "Expert Breaker", "Win an official Expert game."),
        ("challenger", "Challenger", "Complete a friend challenge."),
        ("duelist", "Duelist", "Win a private real-time duel."),
    ]
    achievement_table = sa.table(
        "achievements",
        sa.column("key", sa.String()),
        sa.column("version", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
    )
    op.bulk_insert(
        achievement_table,
        [
            {"key": key, "version": 1, "name": name, "description": description}
            for key, name, description in achievement_rows
        ],
    )
    flag_table = sa.table(
        "feature_flags",
        sa.column("key", sa.String()),
        sa.column("enabled", sa.Boolean()),
        sa.column("description", sa.String()),
    )
    op.bulk_insert(
        flag_table,
        [
            {"key": key, "enabled": True, "description": description}
            for key, description in (
                ("daily", "Official daily challenge"),
                ("leaderboards", "Public leaderboards"),
                ("friend_challenges", "Private asynchronous challenges"),
                ("multiplayer", "Private real-time duels"),
                ("achievements", "Achievement awarding"),
                ("account_registration", "Registered account upgrades"),
                ("analytics", "Privacy-conscious first-party analytics"),
            )
        ],
    )

    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            DO $$ BEGIN
              CREATE ROLE mastermind_runtime NOLOGIN;
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$
            """
        )
        table_privileges = {
            "profiles": "SELECT, INSERT, UPDATE",
            "daily_challenges": "SELECT, INSERT",
            "friend_challenges": "SELECT, INSERT, UPDATE",
            "multiplayer_rooms": "SELECT, INSERT, UPDATE",
            "game_sessions": "SELECT, INSERT, UPDATE",
            "game_attempts": "SELECT, INSERT",
            "multiplayer_members": "SELECT, INSERT, UPDATE",
            "multiplayer_events": "SELECT, INSERT",
            "leaderboard_entries": "SELECT, INSERT, UPDATE",
            "achievements": "SELECT",
            "user_achievements": "SELECT, INSERT, DELETE",
            "feature_flags": "SELECT, UPDATE",
            "moderation_actions": "INSERT",
            "audit_events": "SELECT, INSERT",
            "admin_grants": "SELECT, DELETE",
            "support_requests": "INSERT, DELETE",
            "account_deletion_requests": "SELECT, INSERT, UPDATE",
        }
        for table, privileges in table_privileges.items():
            op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY")
            op.execute(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC")
            op.execute(
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
            )
            op.execute(f"GRANT {privileges} ON TABLE public.{table} TO mastermind_runtime")
            op.execute(
                f"""
                CREATE POLICY mastermind_runtime_all ON public.{table}
                FOR ALL TO mastermind_runtime USING (true) WITH CHECK (true)
                """
            )
        op.execute("ALTER TABLE public.product_events ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON TABLE public.product_events FROM PUBLIC")
        op.execute(
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
        )
        op.execute("GRANT INSERT ON TABLE public.product_events TO mastermind_runtime")
        op.execute(
            """
            CREATE POLICY mastermind_runtime_insert ON public.product_events
            FOR INSERT TO mastermind_runtime WITH CHECK (true)
            """
        )
        op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM PUBLIC")
        op.execute(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC"
        )


def downgrade() -> None:
    for table in [
        "product_events",
        "support_requests",
        "account_deletion_requests",
        "audit_events",
        "moderation_actions",
        "user_achievements",
        "leaderboard_entries",
        "multiplayer_events",
        "multiplayer_members",
        "game_attempts",
        "game_sessions",
        "multiplayer_rooms",
        "friend_challenges",
        "admin_grants",
        "feature_flags",
        "achievements",
        "daily_challenges",
        "profiles",
    ]:
        op.drop_table(table)
