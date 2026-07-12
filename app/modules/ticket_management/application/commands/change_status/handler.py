from __future__ import annotations

from app.modules.ticket_management.application.commands.change_status.command import ChangeStatusCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.modules.ticket_management.domain.enums.status import Status


class ChangeStatusHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: ChangeStatusCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		old_status = ticket.status
		if command.status == Status.IN_PROGRESS:
			ticket.start_progress(command.changed_at)
		elif command.status == Status.PENDING:
			ticket.mark_pending(command.pending_reason or "", command.changed_at)
		elif command.status == Status.RESOLVED:
			ticket.resolve(command.resolution_notes or "", command.changed_at)
		elif command.status == Status.CLOSED:
			ticket.close(command.changed_at)
		else:
			raise ValueError(f"Unsupported status transition: {command.status}")
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			TicketStatusChanged(
				ticket_id=ticket.id,
				old_status=old_status,
				new_status=ticket.status,
				changed_at=command.changed_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
