from __future__ import annotations

from app.modules.ticket_management.application.commands.add_comment_attachment.command import AddCommentAttachmentCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import CommentNotFound, TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.entities.attachment import Attachment
from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded
from app.modules.ticket_management.domain.exceptions import CommentNotFound as DomainCommentNotFound


class AddCommentAttachmentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: AddCommentAttachmentCommand) -> TicketDetailDTO:
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
		try:
			ticket.add_attachment_to_comment(command.comment_id, attachment, command.uploaded_at)
		except DomainCommentNotFound as error:
			raise CommentNotFound() from error
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