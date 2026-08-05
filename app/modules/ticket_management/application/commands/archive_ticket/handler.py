from __future__ import annotations

from app.modules.ticket_management.application.commands.archive_ticket.command import ArchiveTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_archived import TicketArchived


class ArchiveTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: ArchiveTicketCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		ticket.archive(command.archived_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketArchived(
				ticket_id=ticket.id,
				archived_at=command.archived_at,
				actor_id=command.actor_id,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
