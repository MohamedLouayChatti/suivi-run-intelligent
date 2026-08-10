from __future__ import annotations

from typing import Any

from app.modules.auth.application.security.support import ROLE_READ_ALL_PERMISSION, parse_uuid
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy

_SELF_OR_READ_ALL_OPERATIONS = frozenset({"read", "read_permissions"})


class RoleAccessPolicy(InstanceAuthorizationPolicy):
	"""Instance rules for a single role: one's own role, or `role.read_all` for any other.

	Holding a role is treated purely as membership here -- the check is "is this the role I
	am in", not "is my role privileged".  Reading one's own role leaks nothing: GET /auth/me
	already returns the caller's roles and effective permissions by name.
	"""

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		role_id = parse_uuid(resource_id)
		if role_id is None:
			return AuthorizationResult(False, "Invalid role identifier.")

		if operation not in _SELF_OR_READ_ALL_OPERATIONS:
			return AuthorizationResult(False, f"Unknown role operation '{operation}'.")

		if role_id in current_user.role_ids or current_user.has_permission(ROLE_READ_ALL_PERMISSION):
			return AuthorizationResult(True, "")
		return AuthorizationResult(False, "You can only access your own role information.")
