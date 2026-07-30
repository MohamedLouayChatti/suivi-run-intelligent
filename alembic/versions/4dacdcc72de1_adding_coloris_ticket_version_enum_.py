"""adding coloris ticket version enum entries

Revision ID: 4dacdcc72de1
Revises: 0d0e8ed60c21
Create Date: 2026-07-30 13:38:12.555382

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4dacdcc72de1'
down_revision: Union[str, Sequence[str], None] = '0d0e8ed60c21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V6';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V1R4';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V1R6';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V32';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V42';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V41';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V50';"
    )
    op.execute(
        "ALTER TYPE ticket_version ADD VALUE IF NOT EXISTS 'V22';"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
