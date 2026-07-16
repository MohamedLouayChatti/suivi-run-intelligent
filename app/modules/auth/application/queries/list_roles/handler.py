from __future__ import annotations

from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.interfaces.role_read_repository import RoleReadRepository
from app.modules.auth.application.queries.list_roles.query import ListRolesQuery


class ListRolesHandler:
	def __init__(self, read_repository: RoleReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: ListRolesQuery) -> list[RoleDTO]:
		return await self.read_repository.list_roles(query)
