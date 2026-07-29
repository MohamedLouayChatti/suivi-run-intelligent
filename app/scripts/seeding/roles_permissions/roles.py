from __future__ import annotations

from dataclasses import dataclass

from app.scripts.seeding.roles_permissions.permissions import PERMISSIONS_BY_NAME


@dataclass(frozen=True, slots=True)
class RoleDefinition:
	name: str
	permission_names: tuple[str, ...]


SEEDED_ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
	RoleDefinition("Admin", tuple(PERMISSIONS_BY_NAME)),
	RoleDefinition(
		"Support Engineer",
		(
			"user.read",
			"role.read",
			"ticket.read",
			"ticket.assign",
			"ticket.change_priority",
			"ticket.change_status",
			"ticket.transfer_application",
			"ticket.archive",
			"ticket.restore",
			"comment.create",
			"comment.update",
			"comment.delete",
			"attachment.create",
			"attachment.delete",
		),
	),
	RoleDefinition("Support Engineer Supervisor", ()),
)

SEEDED_ROLE_NAMES = frozenset(role.name for role in SEEDED_ROLE_DEFINITIONS)
