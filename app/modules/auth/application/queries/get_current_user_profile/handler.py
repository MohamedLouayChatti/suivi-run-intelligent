from __future__ import annotations

from app.modules.auth.application.dto.current_user_profile_dto import CurrentUserProfileDTO
from app.modules.auth.application.exceptions import UserNotFound
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_current_user_profile.query import GetCurrentUserProfileQuery
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery


class GetCurrentUserProfileHandler:
	def __init__(self, user_read_repository: UserReadRepository, permission_read_repository: PermissionReadRepository) -> None:
		self.user_read_repository = user_read_repository
		self.permission_read_repository = permission_read_repository

	async def handle(self, query: GetCurrentUserProfileQuery) -> CurrentUserProfileDTO:
		user = await self.user_read_repository.get_user(query.user_id)
		if user is None:
			raise UserNotFound()

		role = await self.user_read_repository.get_user_role(query.user_id)
		if role is None:
			raise UserNotFound()
		effective_permissions = await self.permission_read_repository.get_effective_permissions(
			GetEffectivePermissionsQuery(user_id=query.user_id)
		)

		return CurrentUserProfileDTO(
			id=user.id,
			auth_provider_user_id=user.auth_provider_user_id,
			email=user.email,
			display_name=user.display_name,
			avatar_url=user.avatar_url,
			functional_team=user.functional_team,
			role=role,
			application_assignments=user.application_assignments,
			effective_permissions=effective_permissions,
		)
