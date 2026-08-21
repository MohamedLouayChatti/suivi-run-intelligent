"""add roles.requires_primary_application

Revision ID: e8b4d270a915
Revises: d5a3f0c81b62
Create Date: 2026-08-21 09:15:00.000000

Some roles describe someone who runs an application of their own -- an Ingénieur Support, a Chef de
projet -- and cannot meaningfully be held by anyone who runs none. Which roles those are is now a
declared property of the role rather than something read off its name or inferred from the
permissions it bundles: nothing in this codebase branches on a role name, and the Admin role is
seeded with every permission, so any permission-derived reading of "is this a staffed role" would
catch administrators too, who legitimately run no application.

Added with a server_default of false so the column can be NOT NULL on a table that already has rows.
Nothing is backfilled here: the roles seeder is the source of truth for this flag, exactly as it is
for each role's permission set, and re-running it sets the two staffed roles to true.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e8b4d270a915'
down_revision: Union[str, Sequence[str], None] = 'd5a3f0c81b62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adding a NOT NULL column with a constant default needs ACCESS EXCLUSIVE, and a *waiting*
    # request for that lock queues ahead of every new reader -- so a migration blocked behind one
    # idle-in-transaction connection stops the application from reading `roles` at all, for as long
    # as it waits. Failing after five seconds turns that outage into an error message telling you to
    # close the connection.
    op.execute("SET LOCAL lock_timeout = '5s'")

    op.add_column(
        "roles",
        sa.Column("requires_primary_application", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.drop_column("roles", "requires_primary_application")
