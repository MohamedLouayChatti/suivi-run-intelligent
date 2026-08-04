from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.domain.constants import DEFAULT_ROLE_NAME
from app.scripts.seeding.roles_permissions.permissions import PERMISSIONS_BY_NAME


@dataclass(frozen=True, slots=True)
class RoleDefinition:
	name: str
	permission_names: tuple[str, ...]


SEEDED_ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
	RoleDefinition("Admin", tuple(PERMISSIONS_BY_NAME)),
	RoleDefinition(
		"Ingénieur Support",
		(
			"user.read",
			"role.read",
			"ticket.create",
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
		)
	),
)

SEEDED_ROLE_NAMES = frozenset(role.name for role in SEEDED_ROLE_DEFINITIONS)
