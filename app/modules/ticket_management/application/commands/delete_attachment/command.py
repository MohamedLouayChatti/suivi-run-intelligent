from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DeleteAttachmentCommand:
	ticket_id: UUID
	attachment_id: UUID
	deleted_at: datetime
