from __future__ import annotations

from app.modules.ticket_management.application.commands.add_ticket_attachment.command import AddTicketAttachmentCommand
from app.modules.ticket_management.application.commands.attachment_upload_policy import build_storage_path, validate_upload
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded
from app.shared.storage.service import StorageService


class AddTicketAttachmentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher, storage_service: StorageService) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.storage_service = storage_service

	async def handle(self, command: AddTicketAttachmentCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		validate_upload(command.content, command.content_type)
		storage_path = build_storage_path("tickets", command.attachment_id, command.filename)
		await self.storage_service.save(storage_path, command.content)
		attachment = Attachment.create(
			id=command.attachment_id,
			filename=command.filename,
			content_type=command.content_type,
			storage_path=storage_path,
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
				occurred_at=command.uploaded_at,
				actor_id=attachment.uploaded_by,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)