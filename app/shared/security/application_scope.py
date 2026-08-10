from __future__ import annotations

from enum import Enum
from typing import Annotated, TypeVar

from fastapi import Depends

from app.shared.security.current_user import CurrentUser, get_current_user

ApplicationEnum = TypeVar("ApplicationEnum", bound=Enum)


def require_application_scope(breadth_permission: str, application_enum: type[ApplicationEnum]):
	"""Return a dependency resolving how wide a *collection* endpoint may look.

	The collection-level counterpart to `require_instance_permission`: instance
	authorization answers "may the caller touch this one resource", this answers "which
	slice of the collection is the caller entitled to see at all".  Returns `None` when the
	caller holds `breadth_permission` (no restriction -- they may span every application),
	otherwise the applications they are actually assigned to.

	Consumers intersect the result with any explicit `application` filter at the query
	layer, so requesting something out of scope yields an empty result rather than a 403:
	a collection scope is not a failed authorization check, it is simply a narrower window.

	Generic over the target enum because each consuming module owns its own `Application`
	enum (same values, distinct types); the caller's assignments live on Auth's enum and are
	translated by value here.
	"""

	async def dependency(
		current_user: Annotated[CurrentUser, Depends(get_current_user)],
	) -> frozenset[ApplicationEnum] | None:
		if current_user.has_permission(breadth_permission):
			return None
		return frozenset(
			application_enum(assignment.application.value)
			for assignment in current_user.application_assignments
		)

	return dependency
