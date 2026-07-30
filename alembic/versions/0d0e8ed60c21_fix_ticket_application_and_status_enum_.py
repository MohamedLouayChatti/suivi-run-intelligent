"""fix ticket application and status enum labels

Revision ID: 0d0e8ed60c21
Revises: 27f4776225b3
Create Date: 2026-07-29 16:33:04.863478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d0e8ed60c21'
down_revision: Union[str, Sequence[str], None] = '27f4776225b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ticket_application: labels were left as placeholders (APP_1..APP_4) from the
    # initial scaffold instead of the actual Application enum member names.
    op.execute("ALTER TABLE tickets ALTER COLUMN application TYPE varchar USING application::text")
    op.execute("DROP TYPE ticket_application")
    op.execute("CREATE TYPE ticket_application AS ENUM ('FCI', 'COLORIS', 'AERO', 'VIO')")
    op.execute(
        "ALTER TABLE tickets ALTER COLUMN application TYPE ticket_application "
        "USING application::ticket_application"
    )

    # ticket_status: PENDING was renamed to TRANSFERRED in the domain Status enum,
    # but the Postgres enum type was never updated to match.
    op.execute("ALTER TABLE tickets ALTER COLUMN status TYPE varchar USING status::text")
    op.execute("DROP TYPE ticket_status")
    op.execute(
        "CREATE TYPE ticket_status AS ENUM "
        "('OPEN', 'IN_PROGRESS', 'TRANSFERRED', 'RESOLVED', 'CLOSED')"
    )
    op.execute(
        "ALTER TABLE tickets ALTER COLUMN status TYPE ticket_status USING status::ticket_status"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE tickets ALTER COLUMN status TYPE varchar USING status::text")
    op.execute("DROP TYPE ticket_status")
    op.execute(
        "CREATE TYPE ticket_status AS ENUM "
        "('OPEN', 'IN_PROGRESS', 'PENDING', 'RESOLVED', 'CLOSED')"
    )
    op.execute(
        "ALTER TABLE tickets ALTER COLUMN status TYPE ticket_status USING status::ticket_status"
    )

    op.execute("ALTER TABLE tickets ALTER COLUMN application TYPE varchar USING application::text")
    op.execute("DROP TYPE ticket_application")
    op.execute("CREATE TYPE ticket_application AS ENUM ('APP_1', 'APP_2', 'APP_3', 'APP_4')")
    op.execute(
        "ALTER TABLE tickets ALTER COLUMN application TYPE ticket_application "
        "USING application::ticket_application"
    )
