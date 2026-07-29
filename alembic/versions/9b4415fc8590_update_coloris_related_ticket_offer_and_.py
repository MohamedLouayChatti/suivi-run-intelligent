"""Update COLORIS related ticket offer and version enums

Revision ID: 9b4415fc8590
Revises: 07cf4af6ced2
Create Date: 2026-07-29 15:06:19.134364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b4415fc8590'
down_revision: Union[str, Sequence[str], None] = '07cf4af6ced2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE ticket_offer ADD VALUE IF NOT EXISTS 'NOT_SPECIFIED';"
    )

    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'NOT_SPECIFIED';"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
