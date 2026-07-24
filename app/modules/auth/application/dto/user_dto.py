from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId


@dataclass(frozen=True)
class UserDTO:
	id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	display_name: str
	active: bool
	functional_team: FunctionalTeam = FunctionalTeam.SUPPORT
	application_assignments: frozenset[ApplicationAssignment] = field(default_factory=frozenset)
	role_ids: set[UUID] = field(default_factory=set)
	direct_permission_ids: set[UUID] = field(default_factory=set)
	revoked_permission_ids: set[UUID] = field(default_factory=set)

	@classmethod
	def from_user(cls, user: User) -> UserDTO:
		return cls(
			id=user.id,
			auth_provider_user_id=user.auth_provider_user_id,
			email=user.email,
			display_name=user.display_name,
			active=user.active,
			functional_team=user.functional_team,
			application_assignments=frozenset(user.application_assignments),
			role_ids=set(user.role_ids),
			direct_permission_ids=set(user.direct_permission_ids),
			revoked_permission_ids=set(user.revoked_permission_ids),
		)
