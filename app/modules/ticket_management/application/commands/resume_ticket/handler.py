from app.modules.ticket_management.application.commands.resume_ticket.command import ResumeTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.shared.events.event_publisher import EventPublisher

class ResumeTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher): self.uow, self.event_publisher = uow, event_publisher
	async def handle(self, command: ResumeTicketCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None: raise TicketNotFound()
		old = ticket.status; ticket.resume(command.resumed_at); await self.uow.tickets.save(ticket)
		try: await self.uow.commit()
		except Exception: await self.uow.rollback(); raise
		await self.event_publisher.publish(TicketStatusChanged(ticket.id, old, ticket.status, command.resumed_at))
		return TicketDetailDTO.from_ticket(ticket)
