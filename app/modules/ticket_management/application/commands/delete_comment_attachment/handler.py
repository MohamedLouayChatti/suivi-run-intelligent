from __future__ import annotations

from app.modules.ticket_management.application.commands.delete_comment_attachment.command import DeleteCommentAttachmentCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import AttachmentNotFound, CommentNotFound, TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.attachment_deleted import AttachmentDeleted
from app.modules.ticket_management.domain.exceptions import AttachmentNotFound as DomainAttachmentNotFound
from app.modules.ticket_management.domain.exceptions import CommentNotFound as DomainCommentNotFound


class DeleteCommentAttachmentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: DeleteCommentAttachmentCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		try:
			ticket.delete_attachment_from_comment(command.comment_id, command.attachment_id, command.deleted_at)
		except DomainCommentNotFound as error:
			raise CommentNotFound() from error
		except DomainAttachmentNotFound as error:
			raise AttachmentNotFound() from error
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			AttachmentDeleted(
				ticket_id=ticket.id,
				attachment_id=command.attachment_id,
				deleted_at=command.deleted_at,
				actor_id=command.actor_id,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)