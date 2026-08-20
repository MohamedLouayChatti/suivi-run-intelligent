from __future__ import annotations

import logging

from app.modules.auth.domain.enums.application import Application
from app.modules.auth.domain.enums.assignment_type import AssignmentType
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment

logger = logging.getLogger(__name__)

DEFAULT_FUNCTIONAL_TEAM = FunctionalTeam.SUPPORT
"""Team a user starts on when they declared none."""


def parse_declared_organizational_identity(
	declared_application: str | None, declared_functional_team: str | None
) -> tuple[FunctionalTeam, frozenset[ApplicationAssignment]]:
	"""Read a signup form's self-declared application and team as aggregate input.

	Both are optional on the form and neither is trusted here: an applicant types them about
	themselves, and the identity provider hands them back in a bag the signed-in user can go
	on writing to.  Each therefore falls back to its own default independently -- Support,
	and no application at all -- rather than one unusable answer discarding the other.  Both
	defaults describe a real, ordinary state: the aggregate assigns applications "at most"
	one, never exactly one, because a user exists before anyone has staffed them anywhere.

	The declared application becomes the PRIMARY assignment: the form asks which application
	the applicant works on, which is what primary means.  Conferring that on a self-
	declaration is safe because a new user is created inactive and holds the default role,
	which cannot manage its own application.

	Which teams may hold which applications is deliberately not decided here.  That rule
	belongs to the User aggregate, and restating it would give it a second spelling to drift
	from; the handler attempts the pair and falls back again if the aggregate refuses it.
	"""
	functional_team = DEFAULT_FUNCTIONAL_TEAM
	if declared_functional_team:
		try:
			functional_team = FunctionalTeam(declared_functional_team)
		except ValueError:
			logger.warning("Ignoring unrecognised functional team %r declared at signup.", declared_functional_team)

	if not declared_application:
		return functional_team, frozenset()

	try:
		application = Application(declared_application)
	except ValueError:
		logger.warning("Ignoring unrecognised application %r declared at signup.", declared_application)
		return functional_team, frozenset()

	return functional_team, frozenset({ApplicationAssignment(application, AssignmentType.PRIMARY)})
