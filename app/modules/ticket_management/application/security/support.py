from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.domain.enums.application import Application as TicketApplication
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam as TicketFunctionalTeam
from app.shared.security.current_user import CurrentUser

TicketReadRepositoryScope = Callable[[], AbstractAsyncContextManager[TicketReadRepository]]

READ_ANY_APPLICATION_PERMISSION = "ticket.read_any_application"
"""Breadth permission: see and act on tickets outside one's own application assignments.

Covers reading a ticket, commenting on it, and downloading its attachments alike -- all
three are the same underlying reach ("a ticket that is not in my applications"), and were a
single check before this was modelled as a permission.
"""

MANAGE_ANY_PERMISSION = "ticket.manage_any"
"""Breadth permission: act on a ticket one is not the assignee of."""


def parse_uuid(value: object) -> UUID | None:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(str(value))
	except (TypeError, ValueError):
		return None


def has_application_assignment(current_user: CurrentUser, application: TicketApplication) -> bool:
	return any(
		assignment.application.value == application.value
		for assignment in current_user.application_assignments
	)


def is_same_functional_team(current_user: CurrentUser, functional_team: TicketFunctionalTeam) -> bool:
	return current_user.functional_team.value == functional_team.value


def may_reach_application(current_user: CurrentUser, application: TicketApplication) -> bool:
	"""Assigned to the application, or holding the cross-application breadth permission."""
	return has_application_assignment(current_user, application) or current_user.has_permission(READ_ANY_APPLICATION_PERMISSION)
