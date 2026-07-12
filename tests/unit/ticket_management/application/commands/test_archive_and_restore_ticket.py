from __future__ import annotations

import pytest

from app.modules.ticket_management.application.commands.archive_ticket.command import ArchiveTicketCommand
from app.modules.ticket_management.application.commands.archive_ticket.handler import ArchiveTicketHandler
from app.modules.ticket_management.application.commands.restore_ticket.command import RestoreTicketCommand
from app.modules.ticket_management.application.commands.restore_ticket.handler import RestoreTicketHandler
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.domain.events.ticket_archived import TicketArchived
from app.modules.ticket_management.domain.events.ticket_restored import TicketRestored
from app.modules.ticket_management.domain.exceptions import TicketArchived as DomainTicketArchived
from app.modules.ticket_management.domain.exceptions import TicketNotArchived
from tests.unit.ticket_management.domain import factories


class TestArchiveTicketHandler:
	@pytest.mark.asyncio
	async def test_archives_the_ticket_and_saves_it(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ArchiveTicketHandler(uow, event_publisher)

		await handler.handle(ArchiveTicketCommand(ticket_id=ticket.id, archived_at=moment))

		assert ticket.archived_at == moment
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_ticket_archived(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = ArchiveTicketHandler(uow, event_publisher)

		await handler.handle(ArchiveTicketCommand(ticket_id=ticket.id, archived_at=moment))

		assert event_publisher.last == TicketArchived(ticket_id=ticket.id, archived_at=moment)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = ArchiveTicketHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(ArchiveTicketCommand(ticket_id=factories.new_uuid(), archived_at=factories.BASE_TIME))

	@pytest.mark.asyncio
	async def test_archiving_twice_propagates_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_archived_ticket())
		handler = ArchiveTicketHandler(uow, event_publisher)

		with pytest.raises(DomainTicketArchived):
			await handler.handle(ArchiveTicketCommand(ticket_id=ticket.id, archived_at=factories.a_moment_after(ticket.updated_at)))

		assert uow.committed is False
		assert event_publisher.published == []


class TestRestoreTicketHandler:
	@pytest.mark.asyncio
	async def test_restores_the_ticket_and_saves_it(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_archived_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = RestoreTicketHandler(uow, event_publisher)

		await handler.handle(RestoreTicketCommand(ticket_id=ticket.id, restored_at=moment))

		assert ticket.archived_at is None
		assert uow.committed is True

	@pytest.mark.asyncio
	async def test_publishes_ticket_restored(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_archived_ticket())
		moment = factories.a_moment_after(ticket.updated_at)
		handler = RestoreTicketHandler(uow, event_publisher)

		await handler.handle(RestoreTicketCommand(ticket_id=ticket.id, restored_at=moment))

		assert event_publisher.last == TicketRestored(ticket_id=ticket.id, restored_at=moment)

	@pytest.mark.asyncio
	async def test_raises_ticket_not_found_when_ticket_is_missing(self, uow, event_publisher):
		handler = RestoreTicketHandler(uow, event_publisher)

		with pytest.raises(TicketNotFound):
			await handler.handle(RestoreTicketCommand(ticket_id=factories.new_uuid(), restored_at=factories.BASE_TIME))

	@pytest.mark.asyncio
	async def test_restoring_a_non_archived_ticket_propagates_without_committing(self, uow, event_publisher, ticket_repository):
		ticket = ticket_repository.seed(factories.make_ticket())
		handler = RestoreTicketHandler(uow, event_publisher)

		with pytest.raises(TicketNotArchived):
			await handler.handle(RestoreTicketCommand(ticket_id=ticket.id, restored_at=factories.a_moment_after(ticket.updated_at)))

		assert uow.committed is False
		assert event_publisher.published == []
