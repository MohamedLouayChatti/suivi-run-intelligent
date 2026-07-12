from __future__ import annotations

from app.modules.ticket_management.application.commands.create_ticket.command import CreateTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated


class CreateTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: CreateTicketCommand) -> TicketDetailDTO:
		ticket = Ticket.create(
			id=command.ticket_id,
			title=command.title,
			description=command.description,
			priority=command.priority,
			created_at=command.created_at,
			application=command.application,
			assignee_id=command.assignee_id,
		)
		await self.uow.tickets.add(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketCreated(
				ticket_id=ticket.id,
				title=ticket.title,
				description=ticket.description,
				status=ticket.status,
				priority=ticket.priority,
				created_at=ticket.created_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
