from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.ticket_management.domain.entities.ticket import Ticket


class TicketRepository(ABC):
	@abstractmethod
	async def add(self, ticket: Ticket) -> None:
		raise NotImplementedError

	@abstractmethod
	async def get(self, ticket_id: UUID) -> Ticket | None:
		raise NotImplementedError

	@abstractmethod
	async def save(self, ticket: Ticket) -> None:
		raise NotImplementedError

	@abstractmethod
	async def delete(self, ticket_id: UUID) -> None:
		raise NotImplementedError
