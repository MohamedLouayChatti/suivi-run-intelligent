from __future__ import annotations

from typing import Any

from app.modules.auth.application.security.support import UserReadRepositoryScope, is_admin, parse_uuid
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy

_SELF_OR_ADMIN_OPERATIONS = frozenset({"read", "read_roles", "read_direct_permissions", "read_revoked_permissions"})


class UserAccessPolicy(InstanceAuthorizationPolicy):
	def __init__(self, user_repository_scope: UserReadRepositoryScope) -> None:
		self._user_repository_scope = user_repository_scope

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		user_id = parse_uuid(resource_id)
		if user_id is None:
			return AuthorizationResult(False, "Invalid user identifier.")

		if operation in _SELF_OR_ADMIN_OPERATIONS:
			if current_user.id == user_id or await is_admin(self._user_repository_scope, current_user):
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "You can only access your own user information.")

		return AuthorizationResult(False, f"Unknown user operation '{operation}'.")
