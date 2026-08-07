from __future__ import annotations

from app.modules.ticket_management.domain.enums.application import Application


def effective_applications(
	requested: Application | None, allowed_applications: frozenset[Application] | None
) -> frozenset[Application] | None:
	"""Combines an explicit `application` query filter with the caller's own access
	scope, where `allowed_applications=None` means "no restriction" -- not necessarily
	"admin". Today only `require_analytics_applications_scope`'s admin branch happens to
	produce None, but this function doesn't know or care why; it just honors whatever
	scope it's given (an empty frozenset, e.g. a role with zero application
	assignments, is a real and different case: it means "allowed nothing"). If the
	caller requested a specific application outside their scope, the intersection is
	empty -- the query then legitimately returns nothing, same as Ticket Management's
	list/search endpoints, rather than a 403 (this is a collection-level scope, not a
	single-resource authorization check).
	"""
	if requested is not None:
		if allowed_applications is not None:
			return frozenset({requested}) & allowed_applications
		return frozenset({requested})
	return allowed_applications
