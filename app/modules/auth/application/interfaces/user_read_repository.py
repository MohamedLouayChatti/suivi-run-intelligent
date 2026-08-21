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
	async def find_active_user_ids_with_permission(self, permission_name: str) -> set[UUID]:
		"""Every active user whose effective permissions include `permission_name`.

		The bulk counterpart of `get_effective_permissions`, which answers the same question one
		user at a time. It exists for the callers that need an *audience* rather than a decision --
		"who should be told about this" -- and it answers that in the only currency this codebase
		authorizes in. Resolving an audience by role name instead goes stale the moment the
		permission is granted to another role or to a single user, and reads a role as though it
		meant something beyond the permissions it bundles.

		Ids rather than DTOs: nothing needing a broadcast list needs the users themselves, and an
		audience is a set by nature -- somebody reached through their role and again through a
		direct grant is one recipient.

		An unknown permission name yields an empty set rather than raising. This is a lookup over
		reference data a seeder owns, so "nobody holds it" and "it does not exist" call for the
		same answer from a read model: no recipients.
		"""
		raise NotImplementedError

	@abstractmethod
	async def get_user_role(self, user_id: UUID) -> RoleDTO | None:
		"""The one role this user holds, or None when no such user exists.

		None means "no such user", never "no role": a user always holds exactly one.
		"""
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
