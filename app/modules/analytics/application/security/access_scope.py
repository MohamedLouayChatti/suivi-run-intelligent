from __future__ import annotations

from app.modules.ticket_management.domain.enums.application import Application
from app.shared.security.current_user import CurrentUser


def accessible_applications(current_user: CurrentUser) -> frozenset[Application]:
	"""The caller's own assigned applications, translated from Auth's Application enum
	to Ticket Management's -- same values, distinct types (see
	TicketAccessPolicy.allowed_applications_filter for the precedent)."""
	return frozenset(Application(assignment.application.value) for assignment in current_user.application_assignments)
