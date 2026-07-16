from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from app.modules.auth.domain.repositories.permission_repository import PermissionRepository
from app.modules.auth.domain.repositories.role_repository import RoleRepository
from app.modules.auth.domain.repositories.user_repository import UserRepository


class UnitOfWork(ABC):
	users: UserRepository
	roles: RoleRepository
	permissions: PermissionRepository

	@abstractmethod
	async def commit(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def rollback(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def __aenter__(self) -> UnitOfWork:
		raise NotImplementedError

	@abstractmethod
	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc: BaseException | None,
		tb: TracebackType | None,
	) -> None:
		raise NotImplementedError
