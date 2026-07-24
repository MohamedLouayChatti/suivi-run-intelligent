from app.modules.ticket_management.application.commands.transfer_ticket.command import TransferTicketCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.ticket_transferred import TicketTransferred
from app.shared.events.event_publisher import EventPublisher

class TransferTicketHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher): self.uow, self.event_publisher = uow, event_publisher
	async def handle(self, command: TransferTicketCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None: raise TicketNotFound()
		ticket.transfer(command.transferred_to, command.transferred_at); await self.uow.tickets.save(ticket)
		try: await self.uow.commit()
		except Exception: await self.uow.rollback(); raise
		await self.event_publisher.publish(TicketTransferred(ticket.id, ticket.transferred_to, command.transferred_at))
		return TicketDetailDTO.from_ticket(ticket)
