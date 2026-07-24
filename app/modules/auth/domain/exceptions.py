from __future__ import annotations

from app.shared.exceptions.domain_exceptions import DomainError


class AuthorizationDomainError(DomainError):
	"""Base exception for authorization domain errors."""


class PermissionAlreadyGranted(AuthorizationDomainError):
	pass


class PermissionNotGranted(AuthorizationDomainError):
	pass

class InvalidPermissionState(AuthorizationDomainError):
	pass

class InvalidAuthProviderUserId(AuthorizationDomainError):
	pass

class InvalidAssignedRoles(AuthorizationDomainError):
	pass


class InvalidFunctionalTeam(AuthorizationDomainError):
	pass
