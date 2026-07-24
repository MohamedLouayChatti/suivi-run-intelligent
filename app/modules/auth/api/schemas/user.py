from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.domain.enums.application import Application
from app.modules.auth.domain.enums.assignment_type import AssignmentType
from app.modules.auth.domain.enums.functional_team import FunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment


class ApplicationAssignmentSchema(BaseModel):
	application: Application
	assignment_type: AssignmentType

	def to_value_object(self) -> ApplicationAssignment:
		return ApplicationAssignment(self.application, self.assignment_type)


class UserCreateRequest(BaseModel):
	auth_provider_user_id: str = Field(min_length=1)
	email: str = Field(min_length=1)
	display_name: str = Field(min_length=1)
	functional_team: FunctionalTeam = FunctionalTeam.SUPPORT
	application_assignments: list[ApplicationAssignmentSchema] = Field(default_factory=list)


class UserUpdateRequest(BaseModel):
	email: str | None = Field(default=None, min_length=1)
	display_name: str | None = Field(default=None, min_length=1)
	functional_team: FunctionalTeam | None = None
	application_assignments: list[ApplicationAssignmentSchema] | None = None


class UserResponse(BaseModel):
	id: UUID
	auth_provider_user_id: str
	email: str
	display_name: str
	active: bool
	role_ids: set[UUID]
	direct_permission_ids: set[UUID]
	revoked_permission_ids: set[UUID]
	functional_team: FunctionalTeam
	application_assignments: list[ApplicationAssignmentSchema]

	@classmethod
	def from_dto(cls, user: UserDTO) -> UserResponse:
		return cls(
			id=user.id,
			auth_provider_user_id=user.auth_provider_user_id.value,
			email=user.email,
			display_name=user.display_name,
			active=user.active,
			role_ids=user.role_ids,
			direct_permission_ids=user.direct_permission_ids,
			revoked_permission_ids=user.revoked_permission_ids,
			functional_team=user.functional_team,
			application_assignments=[ApplicationAssignmentSchema(application=x.application, assignment_type=x.assignment_type) for x in user.application_assignments],
		)
