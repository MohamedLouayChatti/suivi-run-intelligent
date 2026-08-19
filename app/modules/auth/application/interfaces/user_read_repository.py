from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
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
	async def find_by_display_names(self, display_names: Sequence[str]) -> list[UserDTO]:
		"""Every user whose display name matches one of `display_names`, ignoring case and
		surrounding whitespace.

		Returns the matches rather than a name -> user mapping precisely because `display_name`
		carries no unique constraint: a caller resolving a name to one person has to be able to see
		that two people answer to it. Bulk-shaped for the same reason `get_similarity_summaries`
		is -- the caller holds a file's worth of names, and one round trip is the alternative to
		one query per row.
		"""
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
