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
# `ticket.read_any_application`, `ticket.manage_any`, `ticket.manage_primary_application`,
# `analytics.read_any_application`) are what actually grant reach beyond one's own resources,
# and each is seeded onto whichever roles need it.  Granting one of them to another role --
# or directly to a single user -- is all it takes to delegate that reach; there is no
# separate role gate to satisfy.
_SUPPORT_ENGINEER_PERMISSIONS: tuple[str, ...] = (
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
)

SEEDED_ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
	RoleDefinition("Admin", tuple(PERMISSIONS_BY_NAME)),
	RoleDefinition("Ingénieur Support", _SUPPORT_ENGINEER_PERMISSIONS),
	# A project manager is a support engineer who also runs one application, so the definition
	# says exactly that: the engineer's permissions, plus the knowledge-base maintenance they
	# are responsible for, plus the one breadth permission that widens "the ticket assigned to
	# me" to "any ticket of the application I run".  Nothing about the role name is read
	# anywhere -- the reach comes entirely from `ticket.manage_primary_application`.
	RoleDefinition(
		"Chef de projet",
		_SUPPORT_ENGINEER_PERMISSIONS
		+ (
			"ticket.manage_primary_application",
			"knowledge_base.batch_import",
			"knowledge_base.read_recalculation",
			"knowledge_base.manage_recalculation",
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
