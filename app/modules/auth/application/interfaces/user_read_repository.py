from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.queries.list_users.query import ListUsersQuery


class UserReadRepository(ABC):
	@abstractmethod
	async def get_user(self, user_id: UUID) -> UserDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def get_user_by_auth_provider_user_id(
		self, auth_provider_user_id: str
	) -> UserDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_users(self, query: ListUsersQuery) -> list[UserDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_user_roles(self, user_id: UUID) -> list[RoleDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_user_direct_permissions(
		self, user_id: UUID
	) -> list[PermissionDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_user_revoked_permissions(
		self, user_id: UUID
	) -> list[PermissionDTO]:
		raise NotImplementedError
