from __future__ import annotations

from app.shared.exceptions.exceptions import DomainError


class AuthorizationDomainError(DomainError):
	"""Base exception for authorization domain errors."""


class UserNotFound(AuthorizationDomainError):
	pass


class RoleNotFound(AuthorizationDomainError):
	pass


class PermissionNotFound(AuthorizationDomainError):
	pass


class PermissionAlreadyGranted(AuthorizationDomainError):
	pass


class PermissionNotGranted(AuthorizationDomainError):
	pass

class RoleAlreadyExists(AuthorizationDomainError):
	pass

class InvalidPermissionState(AuthorizationDomainError):
	pass

class InvalidAuthProviderUserId(AuthorizationDomainError):
	pass

class InvalidAssignedRoles(AuthorizationDomainError):
	pass