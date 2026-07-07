from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.entities.attachment import Attachment


@dataclass(frozen=True)
class AttachmentDTO:
	id: UUID
	filename: str
	content_type: str
	storage_path: str
	uploaded_by: UUID
	uploaded_at: datetime
	deleted_at: datetime | None

	@classmethod
	def from_attachment(cls, attachment: Attachment) -> AttachmentDTO:
		return cls(
			id=attachment.id,
			filename=attachment.filename,
			content_type=attachment.content_type,
			storage_path=attachment.storage_path,
			uploaded_by=attachment.uploaded_by,
			uploaded_at=attachment.uploaded_at,
			deleted_at=attachment.deleted_at,
		)
