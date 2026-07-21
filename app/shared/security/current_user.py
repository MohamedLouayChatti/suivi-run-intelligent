from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.api.dependencies import get_auth_provider, get_user_read_repository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.shared.security.auth_provider import AuthProvider


@dataclass(frozen=True, slots=True)
class CurrentUser:
	id: UUID
	auth_provider_user_id: str
	email: str
	display_name: str


_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
	credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
	auth_provider: Annotated[AuthProvider, Depends(get_auth_provider)],
	user_repository: Annotated[UserReadRepository, Depends(get_user_read_repository)],
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
	return CurrentUser(
		id=user.id,
		auth_provider_user_id=user.auth_provider_user_id.value,
		email=user.email,
		display_name=user.display_name,
	)
