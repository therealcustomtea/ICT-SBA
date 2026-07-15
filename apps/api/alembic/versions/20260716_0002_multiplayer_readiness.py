"""Add durable multiplayer readiness and the Comeback achievement.

Revision ID: 20260716_0002
Revises: 20260715_0001
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260716_0002"
down_revision: str | None = "20260715_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("multiplayer_members") as batch_op:
        batch_op.add_column(
            sa.Column(
                "ready",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("ready_at", sa.DateTime(timezone=True)))

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
            {
                "key": "comeback",
                "version": 1,
                "name": "Comeback",
                "description": "Win on the final available attempt.",
            }
        ],
    )


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM user_achievements WHERE achievement_key = 'comeback'"))
    op.execute(sa.text("DELETE FROM achievements WHERE key = 'comeback'"))
    with op.batch_alter_table("multiplayer_members") as batch_op:
        batch_op.drop_column("ready_at")
        batch_op.drop_column("ready")
