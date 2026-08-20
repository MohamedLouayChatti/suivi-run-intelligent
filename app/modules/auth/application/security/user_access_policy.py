from __future__ import annotations

from typing import Any

from app.modules.auth.application.security.support import USER_READ_ALL_PERMISSION, parse_uuid
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy

_SELF_OR_READ_ALL_OPERATIONS = frozenset({"read", "read_role", "read_permissions", "read_revoked_permissions"})

_NEVER_ON_SELF_OPERATIONS = frozenset({"deactivate", "set_role", "revoke_permission", "set_organizational_identity"})


class UserAccessPolicy(InstanceAuthorizationPolicy):
	"""Instance rules for a single user record.

	Reads are self-or-`user.read_all`.  The operations in `_NEVER_ON_SELF_OPERATIONS` are the
	ones that change what the actor themselves may reach, and are refused when the actor is the
	target: without this, the holder of the permission-management permissions can demote their
	own role or deactivate themselves, and -- since roles are fixed reference data with no
	creation endpoint -- nothing short of re-running the seeder can restore access.
	`set_organizational_identity` is refused on the same grounds even though it cannot lock
	anyone out: staffing is a decision made *about* a person, and an administrator who can move
	themselves onto any application also decides, alone, which tickets and analytics they see.
	The rule is deliberately about *self*-targeting only; one administrator restaffing or
	locking out another is recoverable by the other administrators.
	"""

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		user_id = parse_uuid(resource_id)
		if user_id is None:
			return AuthorizationResult(False, "Invalid user identifier.")

		if operation in _SELF_OR_READ_ALL_OPERATIONS:
			if current_user.id == user_id or current_user.has_permission(USER_READ_ALL_PERMISSION):
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "You can only access your own user information.")

		if operation in _NEVER_ON_SELF_OPERATIONS:
			if current_user.id == user_id:
				return AuthorizationResult(False, "You cannot perform this operation on your own account.")
			return AuthorizationResult(True, "")

		return AuthorizationResult(False, f"Unknown user operation '{operation}'.")
