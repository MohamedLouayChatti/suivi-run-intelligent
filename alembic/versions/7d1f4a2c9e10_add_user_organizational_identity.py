"""add user organizational identity"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d1f4a2c9e10"
down_revision: Union[str, Sequence[str], None] = "acd395bfe04f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	functional_team = sa.Enum("SUPPORT", "CONFIGURATION", name="auth_functional_team")
	application = sa.Enum("FCI", "COLORIS", "AERO", "VIO", name="auth_application")
	assignment_type = sa.Enum("PRIMARY", "BACKUP", name="auth_assignment_type")
	functional_team.create(op.get_bind(), checkfirst=True)
	application.create(op.get_bind(), checkfirst=True)
	assignment_type.create(op.get_bind(), checkfirst=True)

	op.add_column("users", sa.Column("functional_team", functional_team, nullable=True))
	op.execute("UPDATE users SET functional_team = 'SUPPORT' WHERE functional_team IS NULL")
	op.alter_column("users", "functional_team", nullable=False)
	op.create_table(
		"user_application_assignments",
		sa.Column("user_id", sa.UUID(), nullable=False),
		sa.Column("application", application, nullable=False),
		sa.Column("assignment_type", assignment_type, nullable=False),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("user_id", "application", "assignment_type"),
	)


def downgrade() -> None:
	op.drop_table("user_application_assignments")
	op.drop_column("users", "functional_team")
	sa.Enum(name="auth_assignment_type").drop(op.get_bind(), checkfirst=True)
	sa.Enum(name="auth_application").drop(op.get_bind(), checkfirst=True)
	sa.Enum(name="auth_functional_team").drop(op.get_bind(), checkfirst=True)
