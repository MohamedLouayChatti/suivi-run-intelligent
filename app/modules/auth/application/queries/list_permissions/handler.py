from __future__ import annotations

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.queries.list_permissions.query import ListPermissionsQuery


class ListPermissionsHandler:
	def __init__(self, read_repository: PermissionReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: ListPermissionsQuery) -> list[PermissionDTO]:
		return await self.read_repository.list_permissions(query)
