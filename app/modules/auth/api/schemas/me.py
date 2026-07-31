from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.modules.auth.api.schemas.permission import PermissionResponse
from app.modules.auth.api.schemas.role import RoleResponse
from app.modules.auth.api.schemas.user import ApplicationAssignmentSchema
from app.modules.auth.application.dto.current_user_profile_dto import CurrentUserProfileDTO
from app.modules.auth.domain.enums.functional_team import FunctionalTeam


class MeResponse(BaseModel):
	id: UUID
	auth_provider_user_id: str
	email: str
	display_name: str
	functional_team: FunctionalTeam
	application_assignments: list[ApplicationAssignmentSchema]
	roles: list[RoleResponse]
	effective_permissions: list[PermissionResponse]

	@classmethod
	def from_dto(cls, profile: CurrentUserProfileDTO) -> MeResponse:
		return cls(
			id=profile.id,
			auth_provider_user_id=profile.auth_provider_user_id.value,
			email=profile.email,
			display_name=profile.display_name,
			functional_team=profile.functional_team,
			application_assignments=[
				ApplicationAssignmentSchema(application=x.application, assignment_type=x.assignment_type)
				for x in profile.application_assignments
			],
			roles=[RoleResponse.from_dto(role) for role in profile.roles],
			effective_permissions=[PermissionResponse.from_dto(permission) for permission in profile.effective_permissions],
		)
