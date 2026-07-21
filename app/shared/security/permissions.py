from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.modules.auth.api.dependencies import get_effective_permissions_handler
from app.modules.auth.application.queries.get_effective_permissions.handler import GetEffectivePermissionsHandler
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery
from app.shared.security.current_user import CurrentUser, get_current_user


def require_permissions(*permissions: str):
	"""Return a dependency requiring every exact permission name provided."""
	if any(permission == "*" for permission in permissions):
		raise ValueError("Wildcard permissions are not supported.")

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
