from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.modules.auth.api.dependencies import get_effective_permissions_handler, get_user_read_repository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_effective_permissions.handler import GetEffectivePermissionsHandler
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery
from app.modules.auth.application.security.support import ADMIN_ROLE_NAME
from app.shared.security.current_user import CurrentUser, get_current_user


def require_permissions(*permissions: str):
	"""Return a dependency requiring every exact permission name provided."""

	async def dependency(
		current_user: Annotated[CurrentUser, Depends(get_current_user)],
		handler: Annotated[GetEffectivePermissionsHandler, Depends(get_effective_permissions_handler)],
	) -> CurrentUser:
		effective = await handler.handle(GetEffectivePermissionsQuery(user_id=current_user.id))
		effective_names = {permission.name for permission in effective}
		if not set(permissions).issubset(effective_names):
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
		return current_user

	return dependency


def require_admin():
	"""Return a dependency requiring the caller to hold the Admin role.

	Distinct from `require_permissions`: a type-level permission grant (e.g. `user.read`)
	only proves the caller may perform that *kind* of read somewhere; it does not imply
	they may see every instance. Collection/global reference-data endpoints (list all
	users, list all roles, anything permission-related) are an Admin-only capability by
	role, not by permission grant, so they must not depend solely on what happens to be
	in the permission catalog for a role.
	"""

	async def dependency(
		current_user: Annotated[CurrentUser, Depends(get_current_user)],
		user_repository: Annotated[UserReadRepository, Depends(get_user_read_repository)],
	) -> CurrentUser:
		roles = await user_repository.get_user_roles(current_user.id)
		if not any(role.name == ADMIN_ROLE_NAME for role in roles):
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required.")
		return current_user

	return dependency
