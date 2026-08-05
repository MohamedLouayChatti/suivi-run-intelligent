from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from app.modules.audit.domain.repositories.audit_entry_repository import AuditEntryRepository


class UnitOfWork(ABC):
	entries: AuditEntryRepository

	@abstractmethod
	async def commit(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def rollback(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def close(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def __aenter__(self) -> Self:
		raise NotImplementedError

	@abstractmethod
	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc: BaseException | None,
		tb: TracebackType | None,
	) -> None:
		raise NotImplementedError
