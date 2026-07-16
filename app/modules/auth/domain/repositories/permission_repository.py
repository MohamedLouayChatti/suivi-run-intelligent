from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.domain.entities.permission import Permission


class PermissionRepository(ABC):
	@abstractmethod
	async def get_by_id(self, permission_id: UUID) -> Permission | None: ...

	@abstractmethod
	async def get_by_name(self, name: str) -> Permission | None: ...

	@abstractmethod
	async def list(self) -> list[Permission]: ...

	@abstractmethod
	async def exists(self, permission_id: UUID) -> bool: ...
