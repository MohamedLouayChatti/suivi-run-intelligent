from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


def require_instance_permission(resource_type: str, operation: str, *, path_param: str):
	"""Return a dependency that delegates instance authorization to a registered policy."""

	async def dependency(
		request: Request,
		current_user: Annotated[CurrentUser, Depends(get_current_user)],
	) -> CurrentUser:
		identifier = request.path_params.get(path_param)
		if identifier is None:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path parameter '{path_param}' is required.")
		registry: InstanceAuthorizationRegistry = request.app.state.instance_authorization_registry
		try:
			policy = registry.resolve(resource_type)
		except KeyError as exc:
			raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Instance authorization policy is not configured.") from exc
		result = await policy.authorize(current_user=current_user, resource_id=identifier, operation=operation)
		if not result.allowed:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result.reason)
		return current_user

	return dependency
