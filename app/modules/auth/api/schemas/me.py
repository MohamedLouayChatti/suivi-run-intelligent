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
	first_name: str
	last_name: str
	display_name: str
	"""The two halves and the composed whole.

	All three, because the settings form edits each half while the header renders the whole
	one, and the frontend must not compose the second from the first: which half leads is a
	rule this application owns, and duplicating it in React is how the two came to disagree.
	"""
	avatar_url: str | None
	functional_team: FunctionalTeam
	application_assignments: list[ApplicationAssignmentSchema]
	role: RoleResponse
	effective_permissions: list[PermissionResponse]

	@classmethod
	def from_dto(cls, profile: CurrentUserProfileDTO) -> MeResponse:
		return cls(
			id=profile.id,
			auth_provider_user_id=profile.auth_provider_user_id.value,
			email=profile.email,
			first_name=profile.first_name,
			last_name=profile.last_name,
			display_name=profile.display_name,
			avatar_url=profile.avatar_url,
			functional_team=profile.functional_team,
			application_assignments=[
				ApplicationAssignmentSchema(application=x.application, assignment_type=x.assignment_type)
				for x in profile.application_assignments
			],
			role=RoleResponse.from_dto(profile.role),
			effective_permissions=[PermissionResponse.from_dto(permission) for permission in profile.effective_permissions],
		)
