from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.domain.value_objects.person_name import compose_display_name


@dataclass(frozen=True)
class CurrentUserProfileDTO:
	id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	first_name: str
	last_name: str
	avatar_url: str | None
	functional_team: FunctionalTeam
	role: RoleDTO
	application_assignments: frozenset[ApplicationAssignment] = field(default_factory=frozenset)
	effective_permissions: list[PermissionDTO] = field(default_factory=list)

	@property
	def display_name(self) -> str:
		"""The composed full name. Carried alongside the two halves rather than instead of
		them: the header renders the whole name, the settings form edits each half, and the
		frontend must not have to compose one from the other -- that rule is the domain's."""
		return compose_display_name(self.first_name, self.last_name)
