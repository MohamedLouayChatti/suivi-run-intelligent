from __future__ import annotations

from app.modules.ticket_management.application.commands.reassign_ticket.command import ReassignTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_reassigned import TicketReassigned


class ReassignTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: ReassignTicketCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		ticket.reassign(command.assignee_id, command.reassigned_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketReassigned(
				ticket_id=ticket.id,
				assignee_id=command.assignee_id,
				reassigned_at=command.reassigned_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
