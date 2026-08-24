# Documents the purpose or contract of this module, class, or function.
"""Add durable game expiry and least-privilege retention access.

Revision ID: 20260716_0003
Revises: 20260716_0002
"""

# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Sequence

# Imports `sqlalchemy as sa` so the module can use that dependency.
import sqlalchemy as sa

# Imports selected names from `alembic` for use in this module.
from alembic import op

# Imports selected names from `sqlalchemy.engine.interfaces` for use in this module.
from sqlalchemy.engine.interfaces import ReflectedColumn

# Computes and stores `revision` for subsequent operations.
revision: str = "20260716_0003"
# Computes and stores `down_revision` for subsequent operations.
down_revision: str | None = "20260716_0002"
# Computes and stores `branch_labels` for subsequent operations.
branch_labels: str | Sequence[str] | None = None
# Computes and stores `depends_on` for subsequent operations.
depends_on: str | Sequence[str] | None = None


# Defines the `_column` callable and its typed interface.
def _column(name: str) -> ReflectedColumn | None:
    # Returns this result to the caller and ends the current function.
    return next(
        # Begins the nested block or multiline expression completed below.
        (
            # Executes this statement as the next step in the surrounding logic.
            item
            # Iterates through the supplied values for the nested operation.
            for item in sa.inspect(op.get_bind()).get_columns("game_sessions")
            # Checks this condition before executing the nested branch.
            if item["name"] == name
            # Closes the multiline call, declaration, or collection started above.
        ),
        # Supplies this item to the surrounding call or collection.
        None,
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_check_names` callable and its typed interface.
def _check_names() -> set[str | None]:
    # Returns this result to the caller and ends the current function.
    return {
        # Executes this statement as the next step in the surrounding logic.
        item["name"]
        # Continues the surrounding expression or operation.
        for item in sa.inspect(op.get_bind()).get_check_constraints("game_sessions")
        # Closes the multiline call, declaration, or collection started above.
    }


# Defines the `_index_names` callable and its typed interface.
def _index_names(table: str = "game_sessions") -> set[str | None]:
    # Returns this result to the caller and ends the current function.
    return {item["name"] for item in sa.inspect(op.get_bind()).get_indexes(table)}


# Computes and stores `RETENTION_INDEXES` for subsequent operations.
RETENTION_INDEXES = {
    # Associates the `game_sessions` key with its value.
    "game_sessions": {
        # Associates the `ix_game_sessions_status_expires` key with its value.
        "ix_game_sessions_status_expires": ["status", "expires_at"],
        # Associates the `ix_game_sessions_completed` key with its value.
        "ix_game_sessions_completed": ["completed_at"],
        # Associates the `ix_game_sessions_friend_completed` key with its value.
        "ix_game_sessions_friend_completed": ["friend_challenge_id", "completed_at"],
        # Associates the `ix_game_sessions_room` key with its value.
        "ix_game_sessions_room": ["room_id"],
        # Closes the multiline call, declaration, or collection started above.
    },
    # Associates the `friend_challenges` key with its value.
    "friend_challenges": {
        # Associates the `ix_friend_challenges_expires` key with its value.
        "ix_friend_challenges_expires": ["expires_at"],
        # Closes the multiline call, declaration, or collection started above.
    },
    # Associates the `multiplayer_rooms` key with its value.
    "multiplayer_rooms": {
        # Associates the `ix_multiplayer_rooms_status_expires` key with its value.
        "ix_multiplayer_rooms_status_expires": ["status", "expires_at"],
        # Associates the `ix_multiplayer_rooms_status_updated` key with its value.
        "ix_multiplayer_rooms_status_updated": ["status", "updated_at"],
        # Closes the multiline call, declaration, or collection started above.
    },
    # Associates the `user_achievements` key with its value.
    "user_achievements": {
        # Associates the `ix_user_achievements_game` key with its value.
        "ix_user_achievements_game": ["game_id"],
        # Closes the multiline call, declaration, or collection started above.
    },
    # Closes the multiline call, declaration, or collection started above.
}


# Defines the `_backfill_expiry` callable and its typed interface.
def _backfill_expiry() -> None:
    # Computes and stores `dialect` for subsequent operations.
    dialect = op.get_bind().dialect.name
    # Checks this condition before executing the nested branch.
    if dialect == "postgresql":
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Calls `sa.text` with the supplied values.
            sa.text(
                # Documents the purpose or contract of this module, class, or function.
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
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
    # Handles the remaining case not matched by earlier branches.
    else:
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Calls `sa.text` with the supplied values.
            sa.text(
                # Documents the purpose or contract of this module, class, or function.
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
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )

    # Calls `op.execute` with the supplied values.
    op.execute(
        # Calls `sa.text` with the supplied values.
        sa.text(
            # Documents the purpose or contract of this module, class, or function.
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
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.execute` with the supplied values.
    op.execute(
        # Calls `sa.text` with the supplied values.
        sa.text(
            # Documents the purpose or contract of this module, class, or function.
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
            # Closes the multiline call, declaration, or collection started above.
        )
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `_grant_postgres_retention_role` callable and its typed interface.
def _grant_postgres_retention_role() -> None:
    # Calls `op.execute` with the supplied values.
    op.execute(
        # Documents the purpose or contract of this module, class, or function.
        """
        DO $$ BEGIN
          CREATE ROLE mastermind_retention NOLOGIN;
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$
        """
        # Closes the multiline call, declaration, or collection started above.
    )
    # Calls `op.execute` with the supplied values.
    op.execute("GRANT USAGE ON SCHEMA public TO mastermind_retention")
    # Computes and stores `privileges` for subsequent operations.
    privileges = {
        # Associates the `game_sessions` key with its value.
        "game_sessions": "SELECT, UPDATE, DELETE",
        # Associates the `game_attempts` key with its value.
        "game_attempts": "SELECT, DELETE",
        # UPDATE privilege is required by PostgreSQL row-locking SELECTs. No
        # UPDATE RLS policy is created for challenges/events, so the role still
        # cannot mutate their contents.
        # Associates the `friend_challenges` key with its value.
        "friend_challenges": "SELECT, UPDATE, DELETE",
        # Associates the `multiplayer_rooms` key with its value.
        "multiplayer_rooms": "SELECT, UPDATE, DELETE",
        # Associates the `multiplayer_members` key with its value.
        "multiplayer_members": "SELECT, DELETE",
        # Associates the `multiplayer_events` key with its value.
        "multiplayer_events": "SELECT, DELETE",
        # Associates the `leaderboard_entries` key with its value.
        "leaderboard_entries": "SELECT, DELETE",
        # Associates the `user_achievements` key with its value.
        "user_achievements": "SELECT, UPDATE",
        # Associates the `product_events` key with its value.
        "product_events": "SELECT, UPDATE, DELETE",
        # Closes the multiline call, declaration, or collection started above.
    }
    # Iterates through the supplied values for the nested operation.
    for table, table_privileges in privileges.items():
        # Calls `op.execute` with the supplied values.
        op.execute(f"GRANT {table_privileges} ON TABLE public.{table} TO mastermind_retention")
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Executes this statement as the next step in the surrounding logic.
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
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Executes this statement as the next step in the surrounding logic.
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
            # Closes the multiline call, declaration, or collection started above.
        )
    # Iterates through the supplied values for the nested operation.
    for table in ("game_sessions", "multiplayer_rooms", "user_achievements"):
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Executes this statement as the next step in the surrounding logic.
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
            # Closes the multiline call, declaration, or collection started above.
        )
    # Iterates through the supplied values for the nested operation.
    for table in ("friend_challenges", "product_events"):
        # Calls `op.execute` with the supplied values.
        op.execute(
            # Executes this statement as the next step in the surrounding logic.
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
            # Closes the multiline call, declaration, or collection started above.
        )


# Defines the `upgrade` callable and its typed interface.
def upgrade() -> None:
    # Computes and stores `expiry_column` for subsequent operations.
    expiry_column = _column("expires_at")
    # Checks this condition before executing the nested branch.
    if expiry_column is None:
        # Calls `op.add_column` with the supplied values.
        op.add_column(
            # Supplies this item to the surrounding call or collection.
            "game_sessions",
            # Calls `sa.Column` with the supplied values.
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            # Closes the multiline call, declaration, or collection started above.
        )
        # Computes and stores `expiry_column` for subsequent operations.
        expiry_column = _column("expires_at")
    # Calls `_backfill_expiry` with the supplied values.
    _backfill_expiry()
    # Checks this condition before executing the nested branch.
    if expiry_column is not None and expiry_column.get("nullable", True):
        # Acquires this managed resource and guarantees cleanup afterward.
        with op.batch_alter_table("game_sessions") as batch_op:
            # Calls `batch_op.alter_column` with the supplied values.
            batch_op.alter_column(
                # Supplies this item to the surrounding call or collection.
                "expires_at",
                # Provides the `existing_type` parameter or keyword argument.
                existing_type=sa.DateTime(timezone=True),
                # Provides the `nullable` parameter or keyword argument.
                nullable=False,
                # Closes the multiline call, declaration, or collection started above.
            )
    # Checks this condition before executing the nested branch.
    if "ck_game_sessions_expiry_after_start" not in _check_names():
        # Acquires this managed resource and guarantees cleanup afterward.
        with op.batch_alter_table("game_sessions") as batch_op:
            # Calls `batch_op.create_check_constraint` with the supplied values.
            batch_op.create_check_constraint("expiry_after_start", "expires_at > started_at")
    # Iterates through the supplied values for the nested operation.
    for table, indexes in RETENTION_INDEXES.items():
        # Computes and stores `existing_indexes` for subsequent operations.
        existing_indexes = _index_names(table)
        # Iterates through the supplied values for the nested operation.
        for index_name, columns in indexes.items():
            # Checks this condition before executing the nested branch.
            if index_name not in existing_indexes:
                # Calls `op.create_index` with the supplied values.
                op.create_index(index_name, table, columns)
    # Checks this condition before executing the nested branch.
    if op.get_bind().dialect.name == "postgresql":
        # Calls `_grant_postgres_retention_role` with the supplied values.
        _grant_postgres_retention_role()


# Defines the `downgrade` callable and its typed interface.
def downgrade() -> None:
    # Checks this condition before executing the nested branch.
    if op.get_bind().dialect.name == "postgresql":
        # Iterates through the supplied values for the nested operation.
        for table in (
            # Supplies this item to the surrounding call or collection.
            "game_sessions",
            # Supplies this item to the surrounding call or collection.
            "game_attempts",
            # Supplies this item to the surrounding call or collection.
            "friend_challenges",
            # Supplies this item to the surrounding call or collection.
            "multiplayer_rooms",
            # Supplies this item to the surrounding call or collection.
            "multiplayer_members",
            # Supplies this item to the surrounding call or collection.
            "multiplayer_events",
            # Supplies this item to the surrounding call or collection.
            "leaderboard_entries",
            # Supplies this item to the surrounding call or collection.
            "user_achievements",
            # Supplies this item to the surrounding call or collection.
            "product_events",
            # Begins the nested block or multiline expression completed below.
        ):
            # Calls `op.execute` with the supplied values.
            op.execute(f"DROP POLICY IF EXISTS mastermind_retention_update ON public.{table}")
            # Calls `op.execute` with the supplied values.
            op.execute(f"DROP POLICY IF EXISTS mastermind_retention_delete ON public.{table}")
            # Calls `op.execute` with the supplied values.
            op.execute(f"DROP POLICY IF EXISTS mastermind_retention_select ON public.{table}")
            # Calls `op.execute` with the supplied values.
            op.execute(f"REVOKE ALL ON TABLE public.{table} FROM mastermind_retention")
        # Calls `op.execute` with the supplied values.
        op.execute("REVOKE USAGE ON SCHEMA public FROM mastermind_retention")
    # Iterates through the supplied values for the nested operation.
    for table, indexes in reversed(RETENTION_INDEXES.items()):
        # Computes and stores `existing_indexes` for subsequent operations.
        existing_indexes = _index_names(table)
        # Iterates through the supplied values for the nested operation.
        for index_name in reversed(indexes):
            # Checks this condition before executing the nested branch.
            if index_name in existing_indexes:
                # Calls `op.drop_index` with the supplied values.
                op.drop_index(index_name, table_name=table)
    # Checks this condition before executing the nested branch.
    if "ck_game_sessions_expiry_after_start" in _check_names():
        # Acquires this managed resource and guarantees cleanup afterward.
        with op.batch_alter_table("game_sessions") as batch_op:
            # Calls `batch_op.drop_constraint` with the supplied values.
            batch_op.drop_constraint("expiry_after_start", type_="check")
    # Checks this condition before executing the nested branch.
    if _column("expires_at") is not None:
        # Acquires this managed resource and guarantees cleanup afterward.
        with op.batch_alter_table("game_sessions") as batch_op:
            # Calls `batch_op.drop_column` with the supplied values.
            batch_op.drop_column("expires_at")
