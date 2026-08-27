from __future__ import annotations

from enum import Enum
from typing import TypeVar

from app.shared.security.current_user import CurrentUser

ApplicationEnum = TypeVar("ApplicationEnum", bound=Enum)


def compute_application_scope(
	current_user: CurrentUser, breadth_permission: str, application_enum: type[ApplicationEnum],
) -> frozenset[ApplicationEnum] | None:
	"""The same computation `app.shared.security.application_scope.require_application_scope`
	performs for a route, as a bare function a tool can call directly (a tool has no FastAPI
	request to build a Depends dependency against). None means unrestricted -- the caller holds
	`breadth_permission` -- otherwise the caller's own assigned applications.
	"""
	if current_user.has_permission(breadth_permission):
		return None
	return frozenset(
		application_enum(assignment.application.value) for assignment in current_user.application_assignments
	)
