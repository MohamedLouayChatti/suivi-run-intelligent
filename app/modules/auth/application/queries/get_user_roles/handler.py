from __future__ import annotations

from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_user_roles.query import GetUserRolesQuery


class GetUserRolesHandler:
	def __init__(self, read_repository: UserReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetUserRolesQuery) -> list[RoleDTO]:
		return await self.read_repository.get_user_roles(query.user_id)
