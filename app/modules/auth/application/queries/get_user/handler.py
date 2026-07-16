from __future__ import annotations

from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.exceptions import UserNotFound
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_user.query import GetUserQuery


class GetUserHandler:
	def __init__(self, read_repository: UserReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetUserQuery) -> UserDTO:
		user = await self.read_repository.get_user(query.user_id)
		if user is None:
			raise UserNotFound()
		return user
