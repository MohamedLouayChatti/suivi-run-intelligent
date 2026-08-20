from __future__ import annotations

from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.exceptions import UserNotFound
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_user_role.query import GetUserRoleQuery


class GetUserRoleHandler:
	def __init__(self, read_repository: UserReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetUserRoleQuery) -> RoleDTO:
		role = await self.read_repository.get_user_role(query.user_id)
		if role is None:
			raise UserNotFound()
		return role
