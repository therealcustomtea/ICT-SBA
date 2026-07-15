"""Add durable game expiry and least-privilege retention access.

Revision ID: 20260716_0003
Revises: 20260716_0002
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine.interfaces import ReflectedColumn

revision: str = "20260716_0003"
down_revision: str | None = "20260716_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column(name: str) -> ReflectedColumn | None:
    return next(
        (
            item
            for item in sa.inspect(op.get_bind()).get_columns("game_sessions")
            if item["name"] == name
        ),
        None,
    )


def _check_names() -> set[str | None]:
    return {
        item["name"] for item in sa.inspect(op.get_bind()).get_check_constraints("game_sessions")
    }


def _index_names(table: str = "game_sessions") -> set[str | None]:
    return {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}


RETENTION_INDEXES = {
    "game_sessions": {
        "ix_game_sessions_status_expires": ["status", "expires_at"],
        "ix_game_sessions_completed": ["completed_at"],
        "ix_game_sessions_friend_completed": ["friend_challenge_id", "completed_at"],
        "ix_game_sessions_room": ["room_id"],
    },
    "friend_challenges": {
        "ix_friend_challenges_expires": ["expires_at"],
    },
    "multiplayer_rooms": {
        "ix_multiplayer_rooms_status_expires": ["status", "expires_at"],
        "ix_multiplayer_rooms_status_updated": ["status", "updated_at"],
    },
    "user_achievements": {
        "ix_user_achievements_game": ["game_id"],
    },
}


def _backfill_expiry() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute(
            sa.text(
                """
                UPDATE game_sessions
                SET expires_at = started_at + CASE mode
                    WHEN 'solo' THEN INTERVAL '7 days'
                    WHEN 'daily' THEN INTERVAL '1 day'
                    WHEN 'practice' THEN INTERVAL '1 day'
                    WHEN 'pass_and_play' THEN INTERVAL '1 day'
                    WHEN 'friend_challenge' THEN INTERVAL '30 days'
                    WHEN 'duel' THEN INTERVAL '2 hours'
                END
                WHERE expires_at IS NULL
                """
            )
        )
    else:
        op.execute(
            sa.text(
                """
                UPDATE game_sessions
                SET expires_at = CASE mode
                    WHEN 'solo' THEN datetime(started_at, '+7 days')
                    WHEN 'daily' THEN datetime(started_at, '+1 day')
                    WHEN 'practice' THEN datetime(started_at, '+1 day')
                    WHEN 'pass_and_play' THEN datetime(started_at, '+1 day')
                    WHEN 'friend_challenge' THEN datetime(started_at, '+30 days')
                    WHEN 'duel' THEN datetime(started_at, '+2 hours')
                END
                WHERE expires_at IS NULL
                """
            )
        )

    op.execute(
        sa.text(
            """
            UPDATE game_sessions
            SET expires_at = (
                SELECT friend_challenges.expires_at
                FROM friend_challenges
                WHERE friend_challenges.id = game_sessions.friend_challenge_id
            )
            WHERE friend_challenge_id IS NOT NULL
              AND (
                  SELECT friend_challenges.expires_at
                  FROM friend_challenges
                  WHERE friend_challenges.id = game_sessions.friend_challenge_id
              ) > started_at
              AND (
                  SELECT friend_challenges.expires_at
                  FROM friend_challenges
                  WHERE friend_challenges.id = game_sessions.friend_challenge_id
              ) < expires_at
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE game_sessions
            SET expires_at = (
                SELECT multiplayer_rooms.expires_at
                FROM multiplayer_rooms
                WHERE multiplayer_rooms.id = game_sessions.room_id
            )
            WHERE room_id IS NOT NULL
              AND (
                  SELECT multiplayer_rooms.expires_at
                  FROM multiplayer_rooms
                  WHERE multiplayer_rooms.id = game_sessions.room_id
              ) > started_at
              AND (
                  SELECT multiplayer_rooms.expires_at
                  FROM multiplayer_rooms
                  WHERE multiplayer_rooms.id = game_sessions.room_id
              ) < expires_at
            """
        )
    )


def _grant_postgres_retention_role() -> None:
    op.execute(
        """
        DO $$ BEGIN
          CREATE ROLE mastermind_retention NOLOGIN;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
        """
    )
    op.execute("GRANT USAGE ON SCHEMA public TO mastermind_retention")
    privileges = {
        "game_sessions": "SELECT, UPDATE, DELETE",
        "game_attempts": "SELECT, DELETE",
        # UPDATE privilege is required by PostgreSQL row-locking SELECTs. No
        # UPDATE RLS policy is created for challenges/events, so the role still
        # cannot mutate their contents.
        "friend_challenges": "SELECT, UPDATE, DELETE",
        "multiplayer_rooms": "SELECT, UPDATE, DELETE",
        "multiplayer_members": "SELECT, DELETE",
        "multiplayer_events": "SELECT, DELETE",
        "leaderboard_entries": "SELECT, DELETE",
        "user_achievements": "SELECT, UPDATE",
        "product_events": "SELECT, UPDATE, DELETE",
    }
    for table, table_privileges in privileges.items():
        op.execute(f"GRANT {table_privileges} ON TABLE public.{table} TO mastermind_retention")
        op.execute(
            f"""
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'public'
                  AND tablename = '{table}'
                  AND policyname = 'mastermind_retention_select'
              ) THEN
                CREATE POLICY mastermind_retention_select ON public.{table}
                FOR SELECT TO mastermind_retention USING (true);
              END IF;
            END $$
            """
        )
        op.execute(
            f"""
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'public'
                  AND tablename = '{table}'
                  AND policyname = 'mastermind_retention_delete'
              ) THEN
                CREATE POLICY mastermind_retention_delete ON public.{table}
                FOR DELETE TO mastermind_retention USING (true);
              END IF;
            END $$
            """
        )
    for table in ("game_sessions", "multiplayer_rooms", "user_achievements"):
        op.execute(
            f"""
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'public'
                  AND tablename = '{table}'
                  AND policyname = 'mastermind_retention_update'
              ) THEN
                CREATE POLICY mastermind_retention_update ON public.{table}
                FOR UPDATE TO mastermind_retention USING (true) WITH CHECK (true);
              END IF;
            END $$
            """
        )
    for table in ("friend_challenges", "product_events"):
        op.execute(
            f"""
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE schemaname = 'public'
                  AND tablename = '{table}'
                  AND policyname = 'mastermind_retention_update'
              ) THEN
                CREATE POLICY mastermind_retention_update ON public.{table}
                FOR UPDATE TO mastermind_retention USING (true) WITH CHECK (false);
              END IF;
            END $$
            """
        )


def upgrade() -> None:
    expiry_column = _column("expires_at")
    if expiry_column is None:
        op.add_column(
            "game_sessions",
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        )
        expiry_column = _column("expires_at")
    _backfill_expiry()
    if expiry_column is not None and expiry_column.get("nullable", True):
        with op.batch_alter_table("game_sessions") as batch_op:
            batch_op.alter_column(
                "expires_at",
                existing_type=sa.DateTime(timezone=True),
                nullable=False,
            )
    if "ck_game_sessions_expiry_after_start" not in _check_names():
        with op.batch_alter_table("game_sessions") as batch_op:
            batch_op.create_check_constraint("expiry_after_start", "expires_at > started_at")
    for table, indexes in RETENTION_INDEXES.items():
        existing_indexes = _index_names(table)
        for index_name, columns in indexes.items():
            if index_name not in existing_indexes:
                op.create_index(index_name, table, columns)
    if op.get_bind().dialect.name == "postgresql":
        _grant_postgres_retention_role()


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        for table in (
            "game_sessions",
            "game_attempts",
            "friend_challenges",
            "multiplayer_rooms",
            "multiplayer_members",
            "multiplayer_events",
            "leaderboard_entries",
            "user_achievements",
            "product_events",
        ):
            op.execute(f"DROP POLICY IF EXISTS mastermind_retention_update ON public.{table}")
            op.execute(f"DROP POLICY IF EXISTS mastermind_retention_delete ON public.{table}")
            op.execute(f"DROP POLICY IF EXISTS mastermind_retention_select ON public.{table}")
            op.execute(f"REVOKE ALL ON TABLE public.{table} FROM mastermind_retention")
        op.execute("REVOKE USAGE ON SCHEMA public FROM mastermind_retention")
    for table, indexes in reversed(RETENTION_INDEXES.items()):
        existing_indexes = _index_names(table)
        for index_name in reversed(indexes):
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name=table)
    if "ck_game_sessions_expiry_after_start" in _check_names():
        with op.batch_alter_table("game_sessions") as batch_op:
            batch_op.drop_constraint("expiry_after_start", type_="check")
    if _column("expires_at") is not None:
        with op.batch_alter_table("game_sessions") as batch_op:
            batch_op.drop_column("expires_at")
