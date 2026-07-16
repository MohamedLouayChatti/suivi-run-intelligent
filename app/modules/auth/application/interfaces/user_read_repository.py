from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.queries.list_users.query import ListUsersQuery


class UserReadRepository(ABC):
	@abstractmethod
	async def get_user(self, user_id: UUID) -> UserDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_users(self, query: ListUsersQuery) -> list[UserDTO]:
		raise NotImplementedError
