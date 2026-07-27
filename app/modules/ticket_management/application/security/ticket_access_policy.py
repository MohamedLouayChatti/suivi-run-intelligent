from __future__ import annotations

from typing import Any

from app.modules.ticket_management.application.security.support import (
	TicketReadRepositoryScope,
	UserReadRepositoryScope,
	has_application_assignment,
	is_admin,
	is_same_functional_team,
	parse_uuid,
)
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy

_ASSIGNEE_ONLY_OPERATIONS = frozenset({"start", "resolve", "close", "resume", "transfer"})
_ASSIGNEE_OR_ADMIN_OPERATIONS = frozenset({"reassign", "change_priority", "archive", "restore"})


class TicketAccessPolicy(InstanceAuthorizationPolicy):
	def __init__(
		self,
		ticket_repository_scope: TicketReadRepositoryScope,
		user_repository_scope: UserReadRepositoryScope,
	) -> None:
		self._ticket_repository_scope = ticket_repository_scope
		self._user_repository_scope = user_repository_scope

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
			if has_application_assignment(current_user, ticket.application) or await is_admin(self._user_repository_scope, current_user):
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "You are not authorized to access this ticket.")

		if operation in _ASSIGNEE_ONLY_OPERATIONS:
			if ticket.assignee_id == current_user.id:
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "Only the ticket assignee can perform this operation.")

		if operation in _ASSIGNEE_OR_ADMIN_OPERATIONS:
			if ticket.assignee_id == current_user.id or await is_admin(self._user_repository_scope, current_user):
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "Only the ticket assignee or an admin can perform this operation.")

		return AuthorizationResult(False, f"Unknown ticket operation '{operation}'.")

	async def authorize_creation(
		self,
		*,
		current_user: CurrentUser,
		application: Application,
		functional_team: FunctionalTeam,
	) -> AuthorizationResult:
		if not has_application_assignment(current_user, application):
			return AuthorizationResult(False, "You are not assigned to this application.")
		if not is_same_functional_team(current_user, functional_team):
			return AuthorizationResult(False, "This ticket does not belong to your functional team.")
		return AuthorizationResult(True, "")

	async def allowed_applications_filter(self, *, current_user: CurrentUser) -> frozenset[Application] | None:
		if await is_admin(self._user_repository_scope, current_user):
			return None
		return frozenset(
			Application(assignment.application.value) for assignment in current_user.application_assignments
		)
