from __future__ import annotations

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.interfaces.role_read_repository import RoleReadRepository
from app.modules.auth.application.queries.get_role_permissions.query import GetRolePermissionsQuery


class GetRolePermissionsHandler:
	def __init__(self, read_repository: RoleReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetRolePermissionsQuery) -> list[PermissionDTO]:
		return await self.read_repository.get_role_permissions(query.role_id)
