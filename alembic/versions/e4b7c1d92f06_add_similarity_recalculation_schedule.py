"""add similarity recalculation schedule

Revision ID: e4b7c1d92f06
Revises: c7e2b91a4d38
Create Date: 2026-08-18 10:00:00.000000

The Knowledge Base's second table, and the only configuration table in this codebase: when the full
similarity graph recalculation runs, as an administrator set it.

It exists because the schedule has to survive a restart and be changeable without one. Everything
else about the pass -- what it recomputes, the similarity threshold, the result cap -- stays pinned
in code, so this table is not a general settings store and should not become one.

Two things are deliberate here. The row is a singleton, enforced by a check constraint rather than
by convention: a second row would be a second answer to "when does the rebuild run", and whichever
one the code read first would quietly win. And **no row is inserted** -- the defaults (Tuesday and
Friday at 20:00 UTC) live in the domain, in
knowledge_base/domain/entities/similarity_recalculation_schedule.py, and an empty table means
nobody has configured anything and those defaults are in force. Seeding a row here would create a
second copy of them that could drift.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4b7c1d92f06'
down_revision: Union[str, Sequence[str], None] = 'c7e2b91a4d38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'similarity_recalculation_schedule',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        # The three-letter cron codes the domain enum is valued as, as a set of days rather than a
        # string to be parsed back apart.
        sa.Column('days_of_week', postgresql.ARRAY(sa.String(length=3)), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=False),
        sa.Column('minute', sa.Integer(), nullable=False),
        # An IANA zone name rather than an offset, so a schedule set for 20:00 local time stays at
        # 20:00 across a daylight-saving change.
        sa.Column('timezone', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('id = 1', name='ck_similarity_recalculation_schedule_singleton'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('similarity_recalculation_schedule')
