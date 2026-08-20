"""add ROLE_CHANGED notification type

Revision ID: b2d0e58a3c14
Revises: a1c9d47f2b03
Create Date: 2026-08-20 09:05:00.000000

A user holds exactly one role now, so gaining and losing one are no longer two things to be told
about: any change to it is a single ROLE_CHANGED notification, published from a single
UserRoleChanged event.

ROLE_ASSIGNED and ROLE_REVOKED stay in the type. Notifications written under the previous model
still carry them, PostgreSQL cannot drop an enum value anyway, and a reader looking at an old
notification should still see what it actually said.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2d0e58a3c14'
down_revision: Union[str, Sequence[str], None] = 'a1c9d47f2b03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'ROLE_CHANGED';"
    )


def downgrade() -> None:
    # PostgreSQL cannot remove a value from an enum type, and notifications written while this
    # revision was applied still reference it.
    pass
