from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from app.modules.ticket_management.domain.repositories.ticket_repository import TicketRepository


class UnitOfWork(ABC):
	tickets: TicketRepository

	@abstractmethod
	async def commit(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def rollback(self) -> None:
		raise NotImplementedError
	
	@abstractmethod 
	async def __aenter__(self) -> "UnitOfWork":
		raise NotImplementedError

	@abstractmethod
	async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
		raise NotImplementedError
