from app.modules.ticket_management.application.commands.close_ticket.command import CloseTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.shared.events.event_publisher import EventPublisher

class CloseTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher): self.uow, self.event_publisher = uow, event_publisher
	async def handle(self, command: CloseTicketCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None: raise TicketNotFound()
		old = ticket.status; ticket.close(command.closed_at); await self.uow.tickets.save(ticket)
		try: await self.uow.commit()
		except Exception: await self.uow.rollback(); raise
		await self.event_publisher.publish(TicketStatusChanged(ticket.id, old, ticket.status, command.closed_at, command.actor_id))
		return TicketDetailDTO.from_ticket(ticket)
