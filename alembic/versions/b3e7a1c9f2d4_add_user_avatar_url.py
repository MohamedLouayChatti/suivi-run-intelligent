"""add user avatar url

Revision ID: b3e7a1c9f2d4
Revises: fa1ffbfbe030
Create Date: 2026-08-04 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3e7a1c9f2d4'
down_revision: Union[str, Sequence[str], None] = 'fa1ffbfbe030'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('avatar_url', sa.String(length=2048), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'avatar_url')
