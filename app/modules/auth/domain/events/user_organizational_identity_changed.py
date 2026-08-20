from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class UserOrganizationalIdentityChanged(DomainEvent):
	"""An administrator restaffed a user: which applications they hold, and on which team.

	One event covering both fields rather than one each, for the same reason `UserRoleChanged`
	is one event rather than a revoke/assign pair: the two are validated together -- AERO and
	VIO admit Support alone -- so there is no moment at which one has changed and the other has
	not, and splitting it would announce a single administrative act twice.

	Carries the whole assignment set on both sides rather than a primary/backup pair: that is
	the shape the aggregate actually holds, and the cardinality rule is the aggregate's to
	state, not this envelope's to encode a second time.
	"""

	user_id: UUID
	previous_functional_team: FunctionalTeam
	new_functional_team: FunctionalTeam
	previous_application_assignments: frozenset[ApplicationAssignment]
	new_application_assignments: frozenset[ApplicationAssignment]
