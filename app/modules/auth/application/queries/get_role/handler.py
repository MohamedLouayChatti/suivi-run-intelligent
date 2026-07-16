from __future__ import annotations

from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.exceptions import RoleNotFound
from app.modules.auth.application.interfaces.role_read_repository import RoleReadRepository
from app.modules.auth.application.queries.get_role.query import GetRoleQuery


class GetRoleHandler:
	def __init__(self, read_repository: RoleReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetRoleQuery) -> RoleDTO:
		role = await self.read_repository.get_role(query.role_id)
		if role is None:
			raise RoleNotFound()
		return role
