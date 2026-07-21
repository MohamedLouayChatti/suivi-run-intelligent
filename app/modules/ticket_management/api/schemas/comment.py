from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.ticket_management.api.schemas.attachment import AttachmentResponse
from app.modules.ticket_management.application.dto.comment_dto import CommentDTO


class CommentCreateRequest(BaseModel):
	author_id: UUID
	content: str


class CommentUpdateRequest(BaseModel):
	content: str


class CommentResponse(BaseModel):
	id: UUID
	author_id: UUID
	content: str
	created_at: datetime
	attachments: list[AttachmentResponse]
	edited_at: datetime | None
	deleted_at: datetime | None

	@classmethod
	def from_dto(cls, comment: CommentDTO) -> CommentResponse:
		return cls(
			id=comment.id,
			author_id=comment.author_id,
			content=comment.content,
			created_at=comment.created_at,
			attachments=[AttachmentResponse.from_dto(item) for item in comment.attachments],
			edited_at=comment.edited_at,
			deleted_at=comment.deleted_at,
		)
