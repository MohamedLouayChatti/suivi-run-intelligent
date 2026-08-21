from __future__ import annotations

from dataclasses import dataclass

from app.modules.auth.domain.constants import DEFAULT_ROLE_NAME
from app.scripts.seeding.roles_permissions.permissions import PERMISSIONS_BY_NAME


@dataclass(frozen=True, slots=True)
class RoleDefinition:
	name: str
	permission_names: tuple[str, ...]
	requires_primary_application: bool = False
	"""Whether nobody may hold this role without an application of their own to run.

	Declared per role rather than derived: it cannot be read off the role's name, because
	nothing in this codebase branches on one, and it cannot be inferred from the permissions
	below, because Admin is seeded with every one of them and administrators legitimately run
	no application.  This flag is the whole definition of "a staffed role" -- `StaffingService`
	reads it and nothing else.
	"""


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

_ADMIN_EXCLUDED_PERMISSIONS: frozenset[str] = frozenset({"ticket.create"})
"""The permissions an administrator is *not* seeded with, despite holding every other one.

`ticket.create` is the one capability whose permission is not sufficient on its own:
`TicketCreationPolicy` requires an assignment to the application the ticket is filed against and
admits no breadth override, deliberately -- filing a ticket for an application you do not work on
is a data-quality question rather than a privilege one.  An administrator legitimately runs no
application, so seeding this onto the role produces a "Créer un ticket" button leading to a form
that can never be submitted: a capability offered and then refused, which is worse than one never
offered.

Not a statement that administrators may never create tickets.  One who *is* staffed on an
application is one direct grant away from it (`permission.grant_to_user`), which is exactly what
the direct permission exceptions are for -- and unlike the role, that grant is made to someone
whose assignments make it usable.
"""

SEEDED_ROLE_DEFINITIONS: tuple[RoleDefinition, ...] = (
	# Every permission except the ones above, which are useless to this role rather than withheld
	# from it.  Nothing in the codebase reads the name "Admin"; this tuple is the whole definition.
	RoleDefinition("Admin", tuple(name for name in PERMISSIONS_BY_NAME if name not in _ADMIN_EXCLUDED_PERMISSIONS)),
	# An engineer works the tickets of the application they are on: TicketCreationPolicy already
	# refuses a ticket for an application they hold no assignment to, so the role without one
	# describes someone who cannot do the job it names.
	RoleDefinition("Ingénieur Support", _SUPPORT_ENGINEER_PERMISSIONS, requires_primary_application=True),
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
		# Doubly so here: `ticket.manage_primary_application` is scoped to the application the
		# holder runs, so without one it widens their reach by exactly nothing.
		requires_primary_application=True,
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
