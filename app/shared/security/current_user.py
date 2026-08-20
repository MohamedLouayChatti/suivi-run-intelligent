from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.api.dependencies import get_auth_provider, get_effective_permissions_handler, get_user_read_repository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_effective_permissions.handler import GetEffectivePermissionsHandler
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery
from app.shared.security.auth_provider import AuthProvider
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment


@dataclass(frozen=True, slots=True)
class CurrentUser:
	id: UUID
	auth_provider_user_id: str
	email: str
	display_name: str
	functional_team: FunctionalTeam
	application_assignments: frozenset[ApplicationAssignment]
	role_id: UUID
	"""Which role the caller holds -- membership data, never a capability.

	Nothing authorizes on this: it exists so `RoleAccessPolicy` can answer "is this the
	caller's *own* role", the same kind of self-ownership question `UserAccessPolicy` asks
	about a user id.  Whether the caller *may do* something is answered solely by
	`permissions` below.
	"""
	permissions: frozenset[str]
	"""Effective permission names (role perms union direct perms, minus revoked).

	Resolved once per request so every downstream check -- `require_permissions` and every
	`InstanceAuthorizationPolicy` alike -- is a set membership test rather than its own
	database round-trip.  This is what lets instance policies ask permission questions
	directly; before, having no way to do so is precisely why they reached for the caller's
	*role* instead.
	"""

	def has_permission(self, permission: str) -> bool:
		return permission in self.permissions


_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
	credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
	auth_provider: Annotated[AuthProvider, Depends(get_auth_provider)],
	user_repository: Annotated[UserReadRepository, Depends(get_user_read_repository)],
	permissions_handler: Annotated[GetEffectivePermissionsHandler, Depends(get_effective_permissions_handler)],
) -> CurrentUser:
	if credentials is None or credentials.scheme.lower() != "bearer":
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
	try:
		claims = auth_provider.authenticate(credentials.credentials)
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.", headers={"WWW-Authenticate": "Bearer"}) from exc

	user = await user_repository.get_user_by_auth_provider_user_id(claims.subject)
	if user is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated user was not found.", headers={"WWW-Authenticate": "Bearer"})
	if not user.active:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated.")

	effective = await permissions_handler.handle(GetEffectivePermissionsQuery(user_id=user.id))
	return CurrentUser(
		id=user.id,
		auth_provider_user_id=user.auth_provider_user_id.value,
		email=user.email,
		display_name=user.display_name,
		functional_team=user.functional_team,
		application_assignments=user.application_assignments,
		role_id=user.role_id,
		permissions=frozenset(permission.name for permission in effective),
	)
