"""add the knowledge base notification types

Revision ID: f2c8a41b7d93
Revises: e8b4d270a915
Create Date: 2026-08-21 12:10:00.000000

Four values, and only one of them is genuinely new.

SIMILARITY_RECALCULATION_COMPLETED is the new one: both outcomes of a full recalculation are now
announced, where success used to be withheld as routine. Announcing only failure left silence
meaning two different things -- a graph that is fine, and a pass that never ran -- for work that is
invisible by construction.

The other three are a **fix**. SIMILARITY_SCHEDULE_UPDATED, SIMILARITY_RECALCULATION_FAILED and
BATCH_IMPORT_FAILED were added to the Python enum when the knowledge base grew its administrative
surface, and no migration ever added them to this type. `notifications.type` is a native PostgreSQL
enum, so writing one of them raised `invalid input value for enum notification_type` -- and because
the in-process event bus logs a failing subscriber and carries on, every one of those notifications
was lost to a log line rather than to an error anybody saw. The three most important things this
module had to say were the three it could not say at all.

Values are added, never removed: PostgreSQL cannot drop an enum value, and notifications already
written reference the ones that are there.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f2c8a41b7d93'
down_revision: Union[str, Sequence[str], None] = 'e8b4d270a915'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# In declaration order, which is also the order they read in: the schedule, then a pass's two
# outcomes, then the import. ADD VALUE runs inside the migration's transaction on PostgreSQL 12+
# so long as nothing uses the new value in that same transaction, which nothing here does.
_ADDED_VALUES = (
    "SIMILARITY_SCHEDULE_UPDATED",
    "SIMILARITY_RECALCULATION_COMPLETED",
    "SIMILARITY_RECALCULATION_FAILED",
    "BATCH_IMPORT_FAILED",
)


def upgrade() -> None:
    for value in _ADDED_VALUES:
        # IF NOT EXISTS because three of these describe a state the database may already be in on
        # an environment where somebody added them by hand to stop the errors.
        op.execute(f"ALTER TYPE notification_type ADD VALUE IF NOT EXISTS '{value}';")


def downgrade() -> None:
    # PostgreSQL cannot remove a value from an enum type, and notifications written while this
    # revision was applied still reference them.
    pass
