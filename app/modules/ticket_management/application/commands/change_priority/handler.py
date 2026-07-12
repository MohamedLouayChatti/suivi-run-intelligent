from __future__ import annotations

from app.modules.ticket_management.application.commands.change_priority.command import ChangePriorityCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.priority_changed import PriorityChanged


class ChangePriorityHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: ChangePriorityCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		old_priority = ticket.priority
		ticket.change_priority(command.priority, command.changed_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			PriorityChanged(
				ticket_id=ticket.id,
				old_priority=old_priority,
				new_priority=command.priority,
				changed_at=command.changed_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
