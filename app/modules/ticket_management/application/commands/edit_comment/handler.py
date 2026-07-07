from __future__ import annotations

from app.modules.ticket_management.application.commands.edit_comment.command import EditCommentCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import CommentNotFound, TicketNotFound
from app.modules.ticket_management.application.interfaces.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.comment_edited import CommentEdited


class EditCommentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: EditCommentCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		comment = next((item for item in ticket.comments if item.id == command.comment_id), None)
		if comment is None:
			raise CommentNotFound()
		comment.edit(command.content, command.edited_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			CommentEdited(
				ticket_id=ticket.id,
				comment_id=comment.id,
				edited_at=command.edited_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
