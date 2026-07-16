from __future__ import annotations

from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.list_users.query import ListUsersQuery


class ListUsersHandler:
	def __init__(self, read_repository: UserReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: ListUsersQuery) -> list[UserDTO]:
		return await self.read_repository.list_users(query)
