"""Extend ticket version enum

Revision ID: 27f4776225b3
Revises: 9b4415fc8590
Create Date: 2026-07-29 15:14:31.186067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27f4776225b3'
down_revision: Union[str, Sequence[str], None] = '9b4415fc8590'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V14';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V15';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V16';"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
