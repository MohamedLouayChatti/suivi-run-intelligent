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

class InvalidAssignedRole(AuthorizationDomainError):
	pass


class InvalidRole(AuthorizationDomainError):
	pass


class InvalidFunctionalTeam(AuthorizationDomainError):
	pass


class FunctionalTeamNotAllowedForApplication(AuthorizationDomainError):
	"""A Configuration engineer was assigned to an application that has no Configuration team."""


class DuplicateApplicationAssignment(AuthorizationDomainError):
	"""One application was assigned to the same user twice, e.g. as both primary and backup."""


class MultiplePrimaryApplications(AuthorizationDomainError):
	"""A user was given more than one primary application; they run at most one."""


class MultipleBackupApplications(AuthorizationDomainError):
	"""A user was given more than one backup application; they back up at most one."""
