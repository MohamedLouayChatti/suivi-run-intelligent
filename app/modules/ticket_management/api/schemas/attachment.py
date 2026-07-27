from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.user_summary_dto import UserSummaryDTO


class UserSummaryResponse(BaseModel):
	id: UUID
	display_name: str

	@classmethod
	def from_dto(cls, user: UserSummaryDTO | None) -> UserSummaryResponse | None:
		return None if user is None else cls(id=user.id, display_name=user.display_name)


class AttachmentCreateRequest(BaseModel):
	filename: str
	content_type: str
	storage_path: str
	uploaded_by: UUID


class AttachmentResponse(BaseModel):
	id: UUID
	filename: str
	content_type: str
	storage_path: str
	uploader: UserSummaryResponse | None
	uploaded_at: datetime
	deleted_at: datetime | None

	@classmethod
	def from_dto(cls, attachment: AttachmentDTO) -> AttachmentResponse:
		return cls(
			id=attachment.id,
			filename=attachment.filename,
			content_type=attachment.content_type,
			storage_path=attachment.storage_path,
			uploader=UserSummaryResponse.from_dto(attachment.uploader),
			uploaded_at=attachment.uploaded_at,
			deleted_at=attachment.deleted_at,
		)
