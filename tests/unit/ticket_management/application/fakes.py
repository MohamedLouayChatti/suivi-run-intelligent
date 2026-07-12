"""
In-memory fakes standing in for infrastructure the application layer
depends on: the ticket repository, the unit of work, and the event
publisher.

These deliberately subclass the real abstract base classes
(`TicketRepository`, `UnitOfWork`, `EventPublisher`) rather than being
unrelated mock objects. That way, if a real interface's method signature
changes, these fakes fail to instantiate and the test suite surfaces the
drift immediately instead of silently testing against a stale contract.

They are intentionally simple (a dict-backed store, list-backed publish
log) since the goal is to observe *interactions* the handlers have with
their dependencies, not to reimplement persistence logic.
"""
from __future__ import annotations

from types import TracebackType
from typing import Self
from uuid import UUID

from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.repositories.ticket_repository import TicketRepository


class FakeTicketRepository(TicketRepository):
	"""An in-memory stand-in for the ticket repository, keyed by ticket id."""

	def __init__(self, tickets: dict[UUID, Ticket] | None = None) -> None:
		self._tickets: dict[UUID, Ticket] = dict(tickets or {})
		self.added: list[Ticket] = []
		self.saved: list[Ticket] = []
		self.deleted_ids: list[UUID] = []

	async def add(self, ticket: Ticket) -> None:
		self._tickets[ticket.id] = ticket
		self.added.append(ticket)

	async def get(self, ticket_id: UUID) -> Ticket | None:
		return self._tickets.get(ticket_id)

	async def save(self, ticket: Ticket) -> None:
		self._tickets[ticket.id] = ticket
		self.saved.append(ticket)

	async def delete(self, ticket_id: UUID) -> None:
		self._tickets.pop(ticket_id, None)
		self.deleted_ids.append(ticket_id)

	def seed(self, ticket: Ticket) -> Ticket:
		"""Convenience for test setup: register a pre-existing ticket."""
		self._tickets[ticket.id] = ticket
		return ticket


class FakeUnitOfWork(UnitOfWork):
	"""
	An in-memory unit of work.

	`fail_commit_with`, when set, makes `commit()` raise that exception once,
	so tests can verify the handler's rollback-and-reraise behavior on
	commit failure.
	"""

	def __init__(self, tickets: FakeTicketRepository | None = None) -> None:
		self.tickets = tickets or FakeTicketRepository()
		self.committed = False
		self.commit_count = 0
		self.rolled_back = False
		self.fail_commit_with: Exception | None = None

	async def commit(self) -> None:
		self.commit_count += 1
		if self.fail_commit_with is not None:
			error, self.fail_commit_with = self.fail_commit_with, None
			raise error
		self.committed = True

	async def rollback(self) -> None:
		self.rolled_back = True

	async def __aenter__(self) -> Self:
		return self

	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc: BaseException | None,
		tb: TracebackType | None,
	) -> None:
		if exc_type is not None:
			await self.rollback()

class FakeEventPublisher(EventPublisher):
	"""Records every event published to it, in order, for later assertion."""

	def __init__(self) -> None:
		self.published: list[object] = []

	async def publish(self, event: object) -> None:
		self.published.append(event)

	@property
	def last(self) -> object:
		return self.published[-1]


class FakeTicketReadRepository(TicketReadRepository):
	"""
	An in-memory stand-in for the read-side repository the query handlers
	depend on.

	Query handlers in this codebase are thin orchestrators (mostly pure
	delegation to this repository), so what matters for testing them is:
	(a) the query object handed to the handler reaches the repository
	unchanged, and (b) whatever the repository returns comes back out of
	the handler unchanged. This fake is built to make both easy to assert:
	`get_ticket`/`list_tickets`/`search_tickets` results are pre-seeded by
	the test, and the last query object received by each method is
	recorded for inspection.

	Filtering/search matching semantics are NOT implemented here on
	purpose: that logic doesn't exist yet in this codebase (it belongs to
	the not-yet-built Infrastructure layer's persistence query), so a fake
	that pretended to filter would be testing behavior nobody has written.
	"""

	def __init__(self) -> None:
		self._tickets_by_id: dict[UUID, TicketDetailDTO] = {}
		self.list_tickets_result: list[TicketSummaryDTO] = []
		self.search_tickets_result: list[TicketSummaryDTO] = []
		self.received_get_ticket_id: UUID | None = None
		self.received_list_query: ListTicketsQuery | None = None
		self.received_search_query: SearchTicketsQuery | None = None

	async def get_ticket(self, ticket_id: UUID) -> TicketDetailDTO | None:
		self.received_get_ticket_id = ticket_id
		return self._tickets_by_id.get(ticket_id)

	async def list_tickets(self, query: ListTicketsQuery) -> list[TicketSummaryDTO]:
		self.received_list_query = query
		return self.list_tickets_result

	async def search_tickets(self, query: SearchTicketsQuery) -> list[TicketSummaryDTO]:
		self.received_search_query = query
		return self.search_tickets_result

	def seed_ticket(self, dto: TicketDetailDTO) -> TicketDetailDTO:
		"""Convenience for test setup: register a pre-existing ticket detail DTO."""
		self._tickets_by_id[dto.id] = dto
		return dto
