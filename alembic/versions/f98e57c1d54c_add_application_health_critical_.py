"""add application health critical notification type

Revision ID: f98e57c1d54c
Revises: 2005c9dde793
Create Date: 2026-08-27 15:12:40.452318

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f98e57c1d54c'
down_revision: Union[str, Sequence[str], None] = '2005c9dde793'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # notifications.type is a native Postgres enum -- adding a Python NotificationType member
    # with no matching migration is a silent no-op at write time (InMemoryEventBus logs the
    # failing subscriber and carries on), the same gap Knowledge Base's own notification types
    # hit before revision f2c8a41b7d93.
    op.execute(
        "ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'APPLICATION_HEALTH_CRITICAL';"
    )


def downgrade() -> None:
    # PostgreSQL cannot remove a value from an enum type, and any row written while this
    # revision was applied still references it.
    pass
