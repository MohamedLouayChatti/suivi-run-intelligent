from __future__ import annotations

import asyncio
from dataclasses import replace
from uuid import UUID

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.comment_dto import CommentDTO
from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.modules.ticket_management.application.dto.user_summary_dto import UserSummaryDTO


class TicketUserEnricher:
	"""Decorates Ticket read DTOs with user projections from Auth."""

	def __init__(self, user_repository: UserReadRepository) -> None:
		self.user_repository = user_repository

	async def _load(self, user_id: UUID | None) -> UserSummaryDTO | None:
		if user_id is None:
			return None
		user = await self.user_repository.get_user(user_id)
		return None if user is None else UserSummaryDTO(id=user.id, display_name=user.display_name)

	async def _load_many(self, user_ids: set[UUID]) -> dict[UUID, UserSummaryDTO | None]:
		values = await asyncio.gather(*(self._load(user_id) for user_id in user_ids))
		return dict(zip(user_ids, values, strict=True))

	async def summaries(self, tickets: list[TicketSummaryDTO]) -> list[TicketSummaryDTO]:
		users = await self._load_many({ticket.assignee_id for ticket in tickets})
		return [replace(ticket, assignee=users.get(ticket.assignee_id)) for ticket in tickets]

	async def detail(self, ticket: TicketDetailDTO) -> TicketDetailDTO:
		user_ids = {ticket.assignee_id}
		user_ids.update(comment.author_id for comment in ticket.comments)
		user_ids.update(attachment.uploaded_by for attachment in ticket.attachments)
		user_ids.update(attachment.uploaded_by for comment in ticket.comments for attachment in comment.attachments)
		users = await self._load_many(user_ids)

		def enrich_attachment(attachment: AttachmentDTO) -> AttachmentDTO:
			return replace(attachment, uploader=users.get(attachment.uploaded_by))

		def enrich_comment(comment: CommentDTO) -> CommentDTO:
			return replace(comment, author=users.get(comment.author_id), attachments=[enrich_attachment(item) for item in comment.attachments])

		return replace(
			ticket,
			assignee=users.get(ticket.assignee_id),
			comments=[enrich_comment(comment) for comment in ticket.comments],
			attachments=[enrich_attachment(attachment) for attachment in ticket.attachments],
		)
