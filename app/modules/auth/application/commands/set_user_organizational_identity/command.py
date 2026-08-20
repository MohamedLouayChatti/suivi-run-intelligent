from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment


@dataclass(frozen=True)
class SetUserOrganizationalIdentityCommand:
	"""Replaces, wholesale, which applications a user holds and which team they are on.

	Both fields are required and neither is a partial update: the two are validated against
	each other, so a caller that could send one alone would be asking the handler to guess the
	other half of a pair the aggregate refuses to see incomplete.  `application_assignments`
	may be empty -- a user who staffs nothing is an ordinary state, and clearing an assignment
	has to be expressible.
	"""

	user_id: UUID
	functional_team: FunctionalTeam
	application_assignments: frozenset[ApplicationAssignment]
	actor_id: UUID
