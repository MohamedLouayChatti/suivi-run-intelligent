from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.exceptions import TicketDomainError


@dataclass
class Attachment:
	id: UUID
	filename: str
	content_type: str
	storage_path: str
	uploaded_by: UUID
	uploaded_at: datetime

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		filename: str,
		content_type: str,
		storage_path: str,
		uploaded_by: UUID,
		uploaded_at: datetime,
	) -> Attachment:
		if not filename.strip() or not content_type.strip() or not storage_path.strip():
			raise TicketDomainError("Attachment metadata is required.")
		return cls(
			id=id,
			filename=filename,
			content_type=content_type,
			storage_path=storage_path,
			uploaded_by=uploaded_by,
			uploaded_at=uploaded_at,
		)
