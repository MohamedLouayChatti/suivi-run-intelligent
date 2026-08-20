"""add ORGANIZATIONAL_IDENTITY_CHANGED notification type

Revision ID: d5a3f0c81b62
Revises: c3f1a86b4e27
Create Date: 2026-08-20 14:10:00.000000

An administrator can now set which applications a user staffs and which functional team they are
on, and the user is told when it changes -- their ticket and analytics scope moves with it.

One value rather than one per field: the application assignments and the functional team are
validated against each other (AERO and VIO admit Support alone), so they are always set together
and there is no change to one of them alone to name.

Values are added, never removed: PostgreSQL cannot drop an enum value, and notifications already
written reference the ones that are there.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5a3f0c81b62'
down_revision: Union[str, Sequence[str], None] = 'c3f1a86b4e27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'ORGANIZATIONAL_IDENTITY_CHANGED';"
    )


def downgrade() -> None:
    # PostgreSQL cannot remove a value from an enum type, and notifications written while this
    # revision was applied still reference it.
    pass
