from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment


@dataclass(frozen=True)
class UpdateUserCommand:
	user_id: UUID
	email: str | None = None
	display_name: str | None = None
	functional_team: FunctionalTeam | None = None
	application_assignments: frozenset[ApplicationAssignment] | None = None
