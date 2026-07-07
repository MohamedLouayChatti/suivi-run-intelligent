from __future__ import annotations

from app.modules.ticket_management.application.commands.delete_attachment.command import DeleteAttachmentCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import AttachmentNotFound, TicketNotFound
from app.modules.ticket_management.application.interfaces.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.attachment_deleted import AttachmentDeleted


class DeleteAttachmentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: DeleteAttachmentCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		attachment = next((item for item in ticket.attachments if item.id == command.attachment_id), None)
		if attachment is None:
			raise AttachmentNotFound()
		attachment.delete(command.deleted_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			AttachmentDeleted(
				ticket_id=ticket.id,
				attachment_id=attachment.id,
				deleted_at=command.deleted_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
