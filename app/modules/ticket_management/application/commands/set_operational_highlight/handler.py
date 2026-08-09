from __future__ import annotations

from app.modules.ticket_management.application.commands.set_operational_highlight.command import SetOperationalHighlightCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.operational_highlight_changed import OperationalHighlightChanged


class SetOperationalHighlightHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: SetOperationalHighlightCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		ticket.set_operational_highlight(command.operational_highlight, command.updated_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			OperationalHighlightChanged(
				ticket_id=ticket.id,
				operational_highlight=ticket.operational_highlight,
				occurred_at=command.updated_at,
				actor_id=command.actor_id,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
