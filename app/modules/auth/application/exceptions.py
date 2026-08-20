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


class DefaultRoleNotFound(AuthorizationApplicationError):
	"""The role every new user is created with is missing from the database.

	Reference data, not a user input problem: roles are seeded, so this only ever means the
	roles/permissions seeder has not been run against this database. Raised rather than
	warned about because a user now holds exactly one mandatory role -- creating them without
	one is no longer a degraded outcome, it is an impossible record.
	"""
