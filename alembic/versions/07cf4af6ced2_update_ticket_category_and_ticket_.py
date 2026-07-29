"""Update ticket_category and ticket_transfer_destination enums

Revision ID: 07cf4af6ced2
Revises: 7d1f4a2c9e10
Create Date: 2026-07-29 14:40:16.671671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07cf4af6ced2'
down_revision: Union[str, Sequence[str], None] = '7d1f4a2c9e10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE ticket_category ADD VALUE IF NOT EXISTS 'CATEGORY_INFRASTRUCTURE';"
    )

    op.execute(
        "ALTER TYPE ticket_transfer_destination ADD VALUE IF NOT EXISTS 'DEVELOPMENT_TEAM';"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
