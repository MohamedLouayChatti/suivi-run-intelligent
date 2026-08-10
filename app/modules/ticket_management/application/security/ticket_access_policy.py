from __future__ import annotations

from typing import Any

from app.modules.ticket_management.application.security.support import (
	MANAGE_ANY_PERMISSION,
	TicketReadRepositoryScope,
	may_reach_application,
	parse_uuid,
)
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy

_ASSIGNEE_ONLY_OPERATIONS = frozenset({"start", "resolve", "close", "resume", "transfer"})
_ASSIGNEE_OR_MANAGE_ANY_OPERATIONS = frozenset({"reassign", "change_priority", "archive", "restore", "update_jira", "update_operational_highlight"})


class TicketAccessPolicy(InstanceAuthorizationPolicy):
	"""Instance rules for one ticket.

	Two distinct axes, each now backed by its own breadth permission rather than by the
	caller's role: *reach* (is this ticket within my applications, or do I hold
	`ticket.read_any_application`) and *ownership* (am I the assignee, or do I hold
	`ticket.manage_any`).  The operations in `_ASSIGNEE_ONLY_OPERATIONS` are workflow
	transitions that only the person actually working the ticket may drive, so they admit no
	breadth override at all.
	"""

	def __init__(self, ticket_repository_scope: TicketReadRepositoryScope) -> None:
		self._ticket_repository_scope = ticket_repository_scope

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		ticket_id = parse_uuid(resource_id)
		if ticket_id is None:
			return AuthorizationResult(False, "Invalid ticket identifier.")

		async with self._ticket_repository_scope() as tickets:
			ticket = await tickets.get_ticket(ticket_id)
		if ticket is None:
			# Let the request through: the handler will raise the proper not-found
			# error. A missing resource is not an authorization outcome.
			return AuthorizationResult(True, "")

		if operation == "read":
			if may_reach_application(current_user, ticket.application):
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "You are not authorized to access this ticket.")

		if operation in _ASSIGNEE_ONLY_OPERATIONS:
			if ticket.assignee_id == current_user.id:
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "Only the ticket assignee can perform this operation.")

		if operation in _ASSIGNEE_OR_MANAGE_ANY_OPERATIONS:
			if ticket.assignee_id == current_user.id or current_user.has_permission(MANAGE_ANY_PERMISSION):
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "Only the ticket assignee, or a user allowed to manage any ticket, can perform this operation.")

		return AuthorizationResult(False, f"Unknown ticket operation '{operation}'.")
