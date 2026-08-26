"""add read only assignment type

Revision ID: 4161bf0a62eb
Revises: 088885cc39b1
Create Date: 2026-08-26 14:16:08.721054

READ_ONLY grants a user reach into an application's tickets, comments, attachments, analytics
and knowledge-base similarity without staffing them there: unlike PRIMARY/BACKUP it does not
require an existing primary, and it is deliberately uncapped (0-N per user), so it gets no
partial unique index of its own.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4161bf0a62eb'
down_revision: Union[str, Sequence[str], None] = '088885cc39b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE auth_assignment_type ADD VALUE IF NOT EXISTS 'READ_ONLY';"
    )


def downgrade() -> None:
    # PostgreSQL cannot remove a value from an enum type, and any row written while this
    # revision was applied still references it.
    pass
