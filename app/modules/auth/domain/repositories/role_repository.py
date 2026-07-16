from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.domain.entities.role import Role


class RoleRepository(ABC):
	@abstractmethod
	async def add(self, role: Role) -> None: ...

	@abstractmethod
	async def get_by_id(self, role_id: UUID) -> Role | None: ...

	@abstractmethod
	async def get_by_name(self, name: str) -> Role | None: ...

	@abstractmethod
	async def update(self, role: Role) -> None: ...

	@abstractmethod
	async def list(self) -> list[Role]: ...
