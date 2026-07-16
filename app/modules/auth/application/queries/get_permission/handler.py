from __future__ import annotations

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.exceptions import PermissionNotFound
from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.queries.get_permission.query import GetPermissionQuery


class GetPermissionHandler:
	def __init__(self, read_repository: PermissionReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetPermissionQuery) -> PermissionDTO:
		permission = await self.read_repository.get_permission(query.permission_id)
		if permission is None:
			raise PermissionNotFound()
		return permission
