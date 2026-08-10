from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.shared.security.current_user import CurrentUser, get_current_user


def require_permissions(*permissions: str):
	"""Return a dependency requiring every exact permission name provided.

	Permissions are the *only* authorization currency in this codebase: a role is nothing
	but a way to grant a set of them, so nothing here (or anywhere else) branches on a role
	name.  Endpoints whose reach exceeds the caller's own resources are gated by an explicit
	breadth permission (`user.read_all`, `ticket.read_any_application`, ...) rather than by
	role membership -- see `app/scripts/seeding/roles_permissions/roles.py`.

	This is a type-level check only: it says the caller may perform this *kind* of operation,
	never on which instances.  Pair it with `require_instance_permission` on any route that
	targets a single resource.

	Reads `CurrentUser.permissions`, already resolved once for the request, so composing
	several of these on one route costs no extra queries.
	"""

	required = frozenset(permissions)

	async def dependency(
		current_user: Annotated[CurrentUser, Depends(get_current_user)],
	) -> CurrentUser:
		if not required.issubset(current_user.permissions):
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
		return current_user

	return dependency
