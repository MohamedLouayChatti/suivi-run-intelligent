from __future__ import annotations

from typing import Any

from app.modules.auth.application.security.support import ADMIN_ROLE_NAME, UserReadRepositoryScope, parse_uuid
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy

_SELF_OR_ADMIN_OPERATIONS = frozenset({"read"})


class RoleAccessPolicy(InstanceAuthorizationPolicy):
	def __init__(self, user_repository_scope: UserReadRepositoryScope) -> None:
		self._user_repository_scope = user_repository_scope

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		role_id = parse_uuid(resource_id)
		if role_id is None:
			return AuthorizationResult(False, "Invalid role identifier.")

		if operation not in _SELF_OR_ADMIN_OPERATIONS:
			return AuthorizationResult(False, f"Unknown role operation '{operation}'.")

		async with self._user_repository_scope() as users:
			roles = await users.get_user_roles(current_user.id)
		if any(role.name == ADMIN_ROLE_NAME or role.id == role_id for role in roles):
			return AuthorizationResult(True, "")
		return AuthorizationResult(False, "You can only access your own role information.")
