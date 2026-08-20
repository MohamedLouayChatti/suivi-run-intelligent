"""one role per user

Revision ID: a1c9d47f2b03
Revises: e4b7c1d92f06
Create Date: 2026-08-20 09:00:00.000000

Replaces the users/roles many-to-many with a single mandatory `users.role_id`.

A role is a named bundle of permissions, and holding several of them made "what may this person
do" answerable only by unioning bundles nobody designed to be combined. The aggregate now owns
exactly one role, so the schema says so too -- a join table left in place would go on permitting a
state the domain refuses to construct, and the read model would have to keep collapsing it.

Collapsing the existing rows keeps the **most** privileged role a user held, measured by how many
permissions it grants, with the role name breaking ties so the result does not depend on row order.
Failing safe on privilege was the wrong default here: roles are seeded reference data with no
creation endpoint, so a user demoted by this migration could only be restored by an administrator,
while a user left over-privileged is one role change away from correct. A user holding no role at
all is given the same default role new users get.

The `role.revoke` permission disappears with the endpoint it gated -- setting a role now implies
replacing the previous one -- but that is a seeded row, not schema: re-running the roles/permissions
seeder is what removes it.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1c9d47f2b03'
down_revision: Union[str, Sequence[str], None] = 'e4b7c1d92f06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Must match app.modules.auth.domain.constants.DEFAULT_ROLE_NAME. Repeated as a literal rather than
# imported: a migration describes the database as it was at this point in history, and importing
# application code would let a later rename silently rewrite what this one did.
DEFAULT_ROLE_NAME = "Lecteur"


def upgrade() -> None:
	op.add_column("users", sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=True))

	op.execute(
		sa.text(
			"""
			WITH ranked AS (
				SELECT
					user_roles.user_id,
					user_roles.role_id,
					ROW_NUMBER() OVER (
						PARTITION BY user_roles.user_id
						ORDER BY
							(
								SELECT count(*)
								FROM role_permissions
								WHERE role_permissions.role_id = user_roles.role_id
							) DESC,
							roles.name ASC
					) AS position
				FROM user_roles
				JOIN roles ON roles.id = user_roles.role_id
			)
			UPDATE users
			SET role_id = ranked.role_id
			FROM ranked
			WHERE ranked.user_id = users.id AND ranked.position = 1
			"""
		)
	)

	op.execute(
		sa.text(
			"""
			UPDATE users
			SET role_id = (SELECT id FROM roles WHERE name = :default_role_name)
			WHERE role_id IS NULL
			"""
		).bindparams(default_role_name=DEFAULT_ROLE_NAME)
	)

	# Only reachable when a user held no role and the default role is not in the database either,
	# which means the roles/permissions seeder has never run here. Stopping with a sentence that
	# says so beats an opaque NOT NULL violation from the next statement.
	orphaned = op.get_bind().scalar(sa.text("SELECT count(*) FROM users WHERE role_id IS NULL"))
	if orphaned:
		raise RuntimeError(
			f"{orphaned} user(s) hold no role and the default role {DEFAULT_ROLE_NAME!r} does not "
			f"exist. Run `python -m app.scripts.seeding.roles_permissions.seed` first, then retry "
			f"this migration."
		)

	op.alter_column("users", "role_id", nullable=False)
	op.create_foreign_key("fk_users_role_id_roles", "users", "roles", ["role_id"], ["id"])
	op.create_index("ix_users_role_id", "users", ["role_id"])

	op.drop_table("user_roles")


def downgrade() -> None:
	op.create_table(
		"user_roles",
		sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
		sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), primary_key=True),
	)
	op.execute(sa.text("INSERT INTO user_roles (user_id, role_id) SELECT id, role_id FROM users"))

	op.drop_index("ix_users_role_id", table_name="users")
	op.drop_constraint("fk_users_role_id_roles", "users", type_="foreignkey")
	op.drop_column("users", "role_id")
