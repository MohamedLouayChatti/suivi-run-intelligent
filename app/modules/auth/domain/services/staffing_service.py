from __future__ import annotations

from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.exceptions import PrimaryApplicationRequiredForRole


class StaffingService:
	"""Checks a user's application staffing against the role they hold.

	Lives beside `AuthorizationService` and for the same reason: the rule spans the User and
	Role aggregates, and validating one aggregate against another inside `User` would make the
	aggregate unable to be constructed without loading a second one.  It is a separate service
	rather than another method on `AuthorizationService` because that one resolves *permissions*
	-- what a person may do -- while this answers whether a person is staffed for the job their
	role describes, which no permission expresses.

	Deliberately has no notion of which roles those are: it reads
	`Role.requires_primary_application` and nothing else, so adding or retiring a staffed role
	is a change to the seeded catalog alone.
	"""

	@staticmethod
	def ensure_staffed_for_role(user: User, role: Role) -> None:
		"""Raise unless the user's own application satisfies what the role requires.

		Checked against `primary_application` alone: a backup assignment is cover for someone
		else's project, and covering a project is not running one -- the same distinction
		`ticket.manage_primary_application` already draws.
		"""
		if role.requires_primary_application and user.primary_application is None:
			raise PrimaryApplicationRequiredForRole()
