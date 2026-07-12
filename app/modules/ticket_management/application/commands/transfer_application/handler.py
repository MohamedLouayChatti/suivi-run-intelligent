from __future__ import annotations

from app.modules.ticket_management.application.commands.transfer_application.command import TransferApplicationCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_transferred import TicketTransferred


class TransferApplicationHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: TransferApplicationCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		old_application = ticket.application
		old_assignee_id = ticket.assignee_id
		ticket.transfer_application(command.new_application, command.new_assignee, command.transferred_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketTransferred(
				ticket_id=ticket.id,
				old_application=old_application,
				new_application=command.new_application,
				old_assignee_id=old_assignee_id,
				new_assignee_id=command.new_assignee,
				transferred_at=command.transferred_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
