# Documents the purpose or contract of this module, class, or function.
"""Add durable multiplayer readiness and the Comeback achievement.

Revision ID: 20260716_0002
Revises: 20260715_0001
"""

# Defers type-annotation evaluation to support modern hints safely.
from __future__ import annotations

# Imports selected names from `collections.abc` for use in this module.
from collections.abc import Sequence

# Imports `sqlalchemy as sa` so the module can use that dependency.
import sqlalchemy as sa

# Imports selected names from `alembic` for use in this module.
from alembic import op

# Computes and stores `revision` for subsequent operations.
revision: str = "20260716_0002"
# Computes and stores `down_revision` for subsequent operations.
down_revision: str | None = "20260715_0001"
# Computes and stores `branch_labels` for subsequent operations.
branch_labels: str | Sequence[str] | None = None
# Computes and stores `depends_on` for subsequent operations.
depends_on: str | Sequence[str] | None = None


# Defines the `upgrade` callable and its typed interface.
def upgrade() -> None:
    # Acquires this managed resource and guarantees cleanup afterward.
    with op.batch_alter_table("multiplayer_members") as batch_op:
        # Calls `batch_op.add_column` with the supplied values.
        batch_op.add_column(
            # Calls `sa.Column` with the supplied values.
            sa.Column(
                # Supplies this item to the surrounding call or collection.
                "ready",
                # Calls `sa.Boolean` with the supplied values.
                sa.Boolean(),
                # Provides the `server_default` parameter or keyword argument.
                server_default=sa.false(),
                # Provides the `nullable` parameter or keyword argument.
                nullable=False,
                # Closes the multiline call, declaration, or collection started above.
            )
            # Closes the multiline call, declaration, or collection started above.
        )
        # Calls `batch_op.add_column` with the supplied values.
        batch_op.add_column(sa.Column("ready_at", sa.DateTime(timezone=True)))

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
            # Begins the nested block or multiline expression completed below.
            {
                # Associates the `key` key with its value.
                "key": "comeback",
                # Associates the `version` key with its value.
                "version": 1,
                # Associates the `name` key with its value.
                "name": "Comeback",
                # Associates the `description` key with its value.
                "description": "Win on the final available attempt.",
                # Closes the multiline call, declaration, or collection started above.
            }
            # Closes the multiline call, declaration, or collection started above.
        ],
        # Closes the multiline call, declaration, or collection started above.
    )


# Defines the `downgrade` callable and its typed interface.
def downgrade() -> None:
    # Calls `op.execute` with the supplied values.
    op.execute(sa.text("DELETE FROM user_achievements WHERE achievement_key = 'comeback'"))
    # Calls `op.execute` with the supplied values.
    op.execute(sa.text("DELETE FROM achievements WHERE key = 'comeback'"))
    # Acquires this managed resource and guarantees cleanup afterward.
    with op.batch_alter_table("multiplayer_members") as batch_op:
        # Calls `batch_op.drop_column` with the supplied values.
        batch_op.drop_column("ready_at")
        # Calls `batch_op.drop_column` with the supplied values.
        batch_op.drop_column("ready")
