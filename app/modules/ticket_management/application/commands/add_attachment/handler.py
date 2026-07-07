from __future__ import annotations

from app.modules.ticket_management.application.commands.add_attachment.command import AddAttachmentCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded


class AddAttachmentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: AddAttachmentCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		attachment = Attachment.create(
			id=command.attachment_id,
			filename=command.filename,
			content_type=command.content_type,
			storage_path=command.storage_path,
			uploaded_by=command.uploaded_by,
			uploaded_at=command.uploaded_at,
		)
		ticket.add_attachment(attachment, command.uploaded_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			AttachmentAdded(
				ticket_id=ticket.id,
				attachment_id=attachment.id,
				uploaded_by=attachment.uploaded_by,
				uploaded_at=command.uploaded_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
