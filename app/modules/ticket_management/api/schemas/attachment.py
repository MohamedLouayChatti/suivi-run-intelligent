from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.user_summary_dto import UserSummaryDTO


class UserSummaryResponse(BaseModel):
	id: UUID
	display_name: str
	avatar_url: str | None

	@classmethod
	def from_dto(cls, user: UserSummaryDTO | None) -> UserSummaryResponse | None:
		return None if user is None else cls(id=user.id, display_name=user.display_name, avatar_url=user.avatar_url)


class AttachmentResponse(BaseModel):
	id: UUID
	filename: str
	content_type: str
	uploader: UserSummaryResponse | None
	uploaded_at: datetime
	deleted_at: datetime | None

	@classmethod
	def from_dto(cls, attachment: AttachmentDTO) -> AttachmentResponse:
		return cls(
			id=attachment.id,
			filename=attachment.filename,
			content_type=attachment.content_type,
			uploader=UserSummaryResponse.from_dto(attachment.uploader),
			uploaded_at=attachment.uploaded_at,
			deleted_at=attachment.deleted_at,
		)
