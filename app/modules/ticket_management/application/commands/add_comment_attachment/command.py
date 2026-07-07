from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AddCommentAttachmentCommand:
	ticket_id: UUID
	comment_id: UUID
	attachment_id: UUID
	filename: str
	content_type: str
	storage_path: str
	uploaded_by: UUID
	uploaded_at: datetime