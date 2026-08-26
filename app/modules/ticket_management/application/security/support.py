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
"""Breadth permission: act on a ticket one is not the assignee of, anywhere."""

MANAGE_PRIMARY_APPLICATION_PERMISSION = "ticket.manage_primary_application"
"""Breadth permission: act on a ticket one is not the assignee of, within one's own project.

The narrow counterpart of `ticket.manage_any`, and the reason a project manager needs no role
of their own in code: they hold every capability an engineer does, plus this, which widens the
same ownership check from "the ticket assigned to me" to "any ticket of the application I run".
Scoped to the PRIMARY assignment alone -- a backup assignment is cover for someone else's
project, and covering it is not managing it.
"""


def parse_uuid(value: object) -> UUID | None:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(str(value))
	except (TypeError, ValueError):
		return None


def has_application_assignment(current_user: CurrentUser, application: TicketApplication) -> bool:
	"""Named here, answered by `CurrentUser`.

	An application assignment belongs to Auth, and this module may not import Auth's domain,
	so the by-value comparison lives on `CurrentUser` -- the one shared type that may name
	Auth's value object. These two read as this module's vocabulary while the rule itself has
	a single spelling.
	"""
	return current_user.has_application_assignment(application)


def has_primary_application_assignment(current_user: CurrentUser, application: TicketApplication) -> bool:
	return current_user.has_primary_application_assignment(application)


def has_actionable_application_assignment(current_user: CurrentUser, application: TicketApplication) -> bool:
	"""Staffed on `application` -- PRIMARY or BACKUP, never a READ_ONLY reach-only assignment."""
	return current_user.has_actionable_application_assignment(application)


def is_same_functional_team(current_user: CurrentUser, functional_team: TicketFunctionalTeam) -> bool:
	return current_user.functional_team.value == functional_team.value


def may_reach_application(current_user: CurrentUser, application: TicketApplication) -> bool:
	"""Assigned to the application, or holding the cross-application breadth permission."""
	return has_application_assignment(current_user, application) or current_user.has_permission(READ_ANY_APPLICATION_PERMISSION)


def may_manage_others_tickets(current_user: CurrentUser, application: TicketApplication) -> bool:
	"""Whether the caller may act on a ticket in `application` that is not assigned to them.

	Two independent ways to qualify, deliberately unranked: unrestricted reach anywhere, or
	reach confined to the one application the caller runs.  Neither is a role -- granting
	either permission to anyone confers exactly the reach it names.
	"""
	return current_user.has_permission(MANAGE_ANY_PERMISSION) or (
		current_user.has_permission(MANAGE_PRIMARY_APPLICATION_PERMISSION)
		and has_primary_application_assignment(current_user, application)
	)
