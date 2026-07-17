from __future__ import annotations

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_user_revoked_permissions.query import GetUserRevokedPermissionsQuery


class GetUserRevokedPermissionsHandler:
	def __init__(self, read_repository: UserReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetUserRevokedPermissionsQuery) -> list[PermissionDTO]:
		return await self.read_repository.get_user_revoked_permissions(query.user_id)
