from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.domain.constants import DEFAULT_ROLE_NAME
from app.scripts.seeding.roles_permissions.permissions import PERMISSIONS_BY_NAME


@dataclass(frozen=True, slots=True)
class RoleDefinition:
	name: str
	permission_names: tuple[str, ...]


# Roles are *only* a way to cluster permissions -- nothing in the codebase branches on a
# role name.  The breadth permissions (`user.read_all`, `role.read_all`,
# `ticket.read_any_application`, `ticket.manage_any`, `analytics.read_any_application`) are
# what actually grant system-wide reach, and they happen to be seeded onto "Admin" alone.
# Granting one of them to another role -- or directly to a single user -- is all it takes to
# delegate that reach; there is no separate role gate to satisfy.
SEEDED_ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
	RoleDefinition("Admin", tuple(PERMISSIONS_BY_NAME)),
	RoleDefinition(
		"Ingénieur Support",
		(
			"user.read",
			"role.read",
			"permission.read",
			"ticket.create",
			"ticket.read",
			"ticket.assign",
			"ticket.change_priority",
			"ticket.change_status",
			"ticket.manage_jira",
			"ticket.manage_highlight",
			"ticket.transfer_application",
			"ticket.archive",
			"ticket.restore",
			"comment.create",
			"comment.update",
			"comment.delete",
			"attachment.create",
			"attachment.delete",
			"attachment.read",
			"notification.read",
			"analytics.read",
		),
	),
	RoleDefinition(
		DEFAULT_ROLE_NAME,
		(
			"user.read",
			"role.read",
			"permission.read",
			"ticket.read",
			"comment.create",
			"comment.update",
			"comment.delete",
			"attachment.create",
			"attachment.delete",
			"attachment.read",
			"notification.read",
			"analytics.read",
		)
	),
)

SEEDED_ROLE_NAMES = frozenset(role.name for role in SEEDED_ROLE_DEFINITIONS)
