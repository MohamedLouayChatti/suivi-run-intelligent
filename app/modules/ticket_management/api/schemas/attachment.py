from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO


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
	uploaded_by: UUID
	uploaded_at: datetime
	deleted_at: datetime | None

	@classmethod
	def from_dto(cls, attachment: AttachmentDTO) -> AttachmentResponse:
		return cls(
			id=attachment.id,
			filename=attachment.filename,
			content_type=attachment.content_type,
			storage_path=attachment.storage_path,
			uploaded_by=attachment.uploaded_by,
			uploaded_at=attachment.uploaded_at,
			deleted_at=attachment.deleted_at,
		)
