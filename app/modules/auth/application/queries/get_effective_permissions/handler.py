from __future__ import annotations

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery


class GetEffectivePermissionsHandler:
	def __init__(self, read_repository: PermissionReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetEffectivePermissionsQuery) -> list[PermissionDTO]:
		return await self.read_repository.get_effective_permissions(query)
