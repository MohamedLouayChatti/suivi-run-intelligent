"""one primary and one backup application per user

Revision ID: c3f1a86b4e27
Revises: b2d0e58a3c14
Create Date: 2026-08-20 11:30:00.000000

Makes `user_application_assignments` say what the business rule always was: a user runs at most one
application and backs up at most one other.

The table's primary key was (user_id, application, assignment_type), which only ever stopped the
identical triple appearing twice. Two different PRIMARY rows, two different BACKUP rows, and the same
application held as both PRIMARY and BACKUP were all permitted, and all describe staffing that does not
exist. Narrowing the key to (user_id, application) settles the last of those -- one assignment per
application per user, with assignment_type an attribute of it rather than part of its identity -- and
the two partial unique indexes settle the other two.

"At most" rather than "exactly": a user is created before anyone has assigned them anywhere, so a user
with no application is an ordinary state and stays one. Nothing is backfilled and nothing is deleted --
no existing row violates any of this.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3f1a86b4e27'
down_revision: Union[str, Sequence[str], None] = 'b2d0e58a3c14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("user_application_assignments_pkey", "user_application_assignments", type_="primary")
    op.create_primary_key(
        "user_application_assignments_pkey", "user_application_assignments", ["user_id", "application"]
    )

    op.create_index(
        "uq_user_application_assignments_one_primary",
        "user_application_assignments",
        ["user_id"],
        unique=True,
        postgresql_where="assignment_type = 'PRIMARY'",
    )
    op.create_index(
        "uq_user_application_assignments_one_backup",
        "user_application_assignments",
        ["user_id"],
        unique=True,
        postgresql_where="assignment_type = 'BACKUP'",
    )


def downgrade() -> None:
    op.drop_index("uq_user_application_assignments_one_backup", table_name="user_application_assignments")
    op.drop_index("uq_user_application_assignments_one_primary", table_name="user_application_assignments")

    op.drop_constraint("user_application_assignments_pkey", "user_application_assignments", type_="primary")
    op.create_primary_key(
        "user_application_assignments_pkey",
        "user_application_assignments",
        ["user_id", "application", "assignment_type"],
    )
