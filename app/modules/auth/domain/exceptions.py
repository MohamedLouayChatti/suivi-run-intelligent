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


class BackupWithoutPrimaryApplication(AuthorizationDomainError):
	"""A user was given a backup application without running one of their own.

	Backing up an application is cover taken on alongside a project of one's own, so a backup
	assignment standing alone describes someone whose whole remit is standing in for other
	people -- a position that does not exist here.
	"""


class PrimaryApplicationRequiredForRole(AuthorizationDomainError):
	"""A role only meaningful for someone running an application was given to someone who runs none.

	Which roles those are is declared on the Role itself (`requires_primary_application`), so
	this is never a statement about any particular role name.
	"""
