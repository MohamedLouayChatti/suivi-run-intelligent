from __future__ import annotations

from app.modules.ticket_management.application.commands.add_comment.command import AddCommentCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.interfaces.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.entities.comment import Comment
from app.modules.ticket_management.domain.events.comment_added import CommentAdded


class AddCommentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: AddCommentCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		comment = Comment.create(
			id=command.comment_id,
			author_id=command.author_id,
			content=command.content,
			created_at=command.created_at,
		)
		ticket.add_comment(comment, command.created_at)
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			CommentAdded(
				ticket_id=ticket.id,
				comment_id=comment.id,
				author_id=comment.author_id,
				created_at=command.created_at,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
