from __future__ import annotations

from app.shared.exceptions.application_exceptions import ApplicationError

class AuthorizationApplicationError(ApplicationError):
	"""Base exception for authorization application errors."""


class UserNotFound(AuthorizationApplicationError):
	pass


class RoleNotFound(AuthorizationApplicationError):
	pass


class PermissionNotFound(AuthorizationApplicationError):
	pass


class RoleAlreadyExists(AuthorizationApplicationError):
	pass
