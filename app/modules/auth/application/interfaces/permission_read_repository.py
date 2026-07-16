from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.queries.get_effective_permissions.query import GetEffectivePermissionsQuery
from app.modules.auth.application.queries.list_permissions.query import ListPermissionsQuery


class PermissionReadRepository(ABC):
	@abstractmethod
	async def get_permission(self, permission_id: UUID) -> PermissionDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_permissions(self, query: ListPermissionsQuery) -> list[PermissionDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_effective_permissions(self, query: GetEffectivePermissionsQuery) -> list[PermissionDTO]:
		raise NotImplementedError
