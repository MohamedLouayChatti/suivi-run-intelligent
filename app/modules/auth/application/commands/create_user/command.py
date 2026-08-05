from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment


@dataclass(frozen=True)
class CreateUserCommand:
	user_id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	display_name: str
	avatar_url: str | None = None
	functional_team: FunctionalTeam = FunctionalTeam.SUPPORT
	application_assignments: frozenset[ApplicationAssignment] = frozenset()
	actor_id: UUID | None = None
