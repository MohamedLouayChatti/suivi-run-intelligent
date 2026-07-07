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

from uuid import UUID

from app.modules.ticket_management.application.interfaces.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
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


class FakeEventPublisher(EventPublisher):
	"""Records every event published to it, in order, for later assertion."""

	def __init__(self) -> None:
		self.published: list[object] = []

	async def publish(self, event: object) -> None:
		self.published.append(event)

	@property
	def last(self) -> object:
		return self.published[-1]
