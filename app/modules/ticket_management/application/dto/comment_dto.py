from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.domain.entities.comment import Comment


@dataclass(frozen=True)
class CommentDTO:
	id: UUID
	author_id: UUID
	content: str
	created_at: datetime
	attachments: list[AttachmentDTO] = field(default_factory=list)
	edited_at: datetime | None = None
	deleted_at: datetime | None = None

	@classmethod
	def from_comment(cls, comment: Comment) -> CommentDTO:
		return cls(
			id=comment.id,
			author_id=comment.author_id,
			content=comment.content,
			created_at=comment.created_at,
			attachments=[AttachmentDTO.from_attachment(attachment) for attachment in comment.attachments],
			edited_at=comment.edited_at,
			deleted_at=comment.deleted_at,
		)
