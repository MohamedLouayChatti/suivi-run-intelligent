from __future__ import annotations

from app.modules.ticket_management.application.security.support import has_actionable_application_assignment, is_same_functional_team
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser


class TicketCreationPolicy:
	"""Whether the caller may create a ticket with the given application/team.

	Deliberately *not* an `InstanceAuthorizationPolicy`: there is no instance yet, so there
	is no `resource_id` to authorize against.  It previously lived on `TicketAccessPolicy`
	and was reached by resolving that policy from the instance registry and `cast()`-ing it
	back to its concrete type -- calling a method the interface does not declare.  Keeping it
	as its own small type lets the API layer depend on it directly and honestly.

	No breadth override here: creating a ticket for an application you are not assigned to,
	or for another functional team, is a data-quality question rather than a privilege one.

	Requires an *actionable* assignment (PRIMARY or BACKUP): a READ_ONLY assignment grants reach
	into an application without staffing, and creating a ticket is staffing's job.
	"""

	async def authorize(
		self,
		*,
		current_user: CurrentUser,
		application: Application,
		functional_team: FunctionalTeam,
	) -> AuthorizationResult:
		if not has_actionable_application_assignment(current_user, application):
			return AuthorizationResult(False, "You are not assigned to this application.")
		if not is_same_functional_team(current_user, functional_team):
			return AuthorizationResult(False, "This ticket does not belong to your functional team.")
		return AuthorizationResult(True, "")
