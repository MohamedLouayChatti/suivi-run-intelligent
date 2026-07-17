from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.queries.list_roles.query import ListRolesQuery


class RoleReadRepository(ABC):
	@abstractmethod
	async def get_role(self, role_id: UUID) -> RoleDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_roles(self, query: ListRolesQuery) -> list[RoleDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_role_permissions(self, role_id: UUID) -> list[PermissionDTO]:
		raise NotImplementedError
