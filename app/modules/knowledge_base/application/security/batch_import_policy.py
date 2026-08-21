from __future__ import annotations

from app.modules.ticket_management.domain.enums.application import Application
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser

IMPORT_ANY_APPLICATION_PERMISSION = "knowledge_base.import_any_application"
"""Breadth permission: load a file of tickets for an application one does not run.

The counterpart of `ticket.read_any_application` and `analytics.read_any_application`, and its
own permission rather than a reuse of either: those two widen what their holder may *see*, while
this widens what they may *create*, several thousand tickets at a time. Seeded onto Admin alone,
which -- as ever -- is where it happens to be granted rather than a role check; granting it to
another role, or to one user, confers exactly the reach it names.
"""


class BatchImportPolicy:
	"""Whether the caller may load a file of tickets for the given application.

	Deliberately *not* an `InstanceAuthorizationPolicy`, for the same reason `TicketCreationPolicy`
	is not one: an import creates resources rather than acting on one, so there is no `resource_id`
	to authorize against. It is a plain class the API layer constructs and calls directly.

	The narrow qualification is the PRIMARY assignment alone, not any assignment. Bulk-loading an
	application's historical incidents decides what its whole corpus says and what every future
	similarity suggestion is drawn from, which is a decision about the project rather than work
	inside it -- the same line `ticket.manage_primary_application` draws, where a backup assignment
	is cover for someone else's project and covering it is not running it.

	This check exists because `knowledge_base.batch_import` is no longer held by administrators
	alone: Chef de projet holds it too, and without an application check a project manager for one
	application could create thousands of tickets against another.
	"""

	async def authorize(self, *, current_user: CurrentUser, application: Application) -> AuthorizationResult:
		if current_user.has_permission(IMPORT_ANY_APPLICATION_PERMISSION):
			return AuthorizationResult(True, "")
		if current_user.has_primary_application_assignment(application):
			return AuthorizationResult(True, "")
		return AuthorizationResult(False, "You may only import tickets for the application you are assigned to run.")
