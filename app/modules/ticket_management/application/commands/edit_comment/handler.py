from __future__ import annotations

from app.modules.ticket_management.application.commands.edit_comment.command import EditCommentCommand
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO
from app.modules.ticket_management.application.exceptions import CommentNotFound, TicketNotFound
from app.shared.events.event_publisher import EventPublisher
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.exceptions import CommentNotFound as DomainCommentNotFound
from app.modules.ticket_management.domain.events.comment_edited import CommentEdited


class EditCommentHandler:
	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: EditCommentCommand) -> TicketDetailDTO:
		ticket = await self.uow.tickets.get(command.ticket_id)
		if ticket is None:
			raise TicketNotFound()
		try:
			ticket.edit_comment(command.comment_id, command.content, command.edited_at)
		except DomainCommentNotFound as error:
			raise CommentNotFound() from error
		await self.uow.tickets.save(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise
		await self.event_publisher.publish(
			CommentEdited(
				ticket_id=ticket.id,
				comment_id=command.comment_id,
				edited_at=command.edited_at,
				actor_id=command.actor_id,
			)
		)
		return TicketDetailDTO.from_ticket(ticket)
