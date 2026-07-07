from __future__ import annotations

from app.modules.ticket_management.application.commands.assign_ticket.command import AssignTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_assigned import TicketAssigned


class AssignTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: AssignTicketCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		ticket.assign(command.assignee_id, command.assigned_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketAssigned(
				ticket_id=ticket.id,
				assignee_id=command.assignee_id,
				assigned_at=command.assigned_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
