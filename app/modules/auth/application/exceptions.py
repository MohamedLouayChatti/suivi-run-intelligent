from __future__ import annotations


class AuthorizationApplicationError(Exception):
	"""Base exception for authorization application errors."""


class UserNotFound(AuthorizationApplicationError):
	pass


class RoleNotFound(AuthorizationApplicationError):
	pass


class PermissionNotFound(AuthorizationApplicationError):
	pass


class RoleAlreadyExists(AuthorizationApplicationError):
	pass
