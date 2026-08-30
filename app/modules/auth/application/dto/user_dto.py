from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.domain.value_objects.person_name import compose_display_name


@dataclass(frozen=True)
class UserDTO:
	id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	first_name: str
	last_name: str
	active: bool
	role_id: UUID
	avatar_url: str | None = None
	functional_team: FunctionalTeam = FunctionalTeam.SUPPORT
	application_assignments: frozenset[ApplicationAssignment] = field(default_factory=frozenset)
	direct_permission_ids: set[UUID] = field(default_factory=set)
	revoked_permission_ids: set[UUID] = field(default_factory=set)

	@property
	def display_name(self) -> str:
		"""The composed full name, spelled by the same domain rule the aggregate uses.

		A property rather than a field so that every module reading a user through this DTO --
		Ticket Management, Analytics, Audit, the assistant's tools -- keeps asking for the name
		exactly as it did when one column held it, and none of them has to learn which half
		goes first.
		"""
		return compose_display_name(self.first_name, self.last_name)

	@classmethod
	def from_user(cls, user: User) -> UserDTO:
		return cls(
			id=user.id,
			auth_provider_user_id=user.auth_provider_user_id,
			email=user.email,
			first_name=user.first_name,
			last_name=user.last_name,
			active=user.active,
			role_id=user.role_id,
			avatar_url=user.avatar_url,
			functional_team=user.functional_team,
			application_assignments=frozenset(user.application_assignments),
			direct_permission_ids=set(user.direct_permission_ids),
			revoked_permission_ids=set(user.revoked_permission_ids),
		)
