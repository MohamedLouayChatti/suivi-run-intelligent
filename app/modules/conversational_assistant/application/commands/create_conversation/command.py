from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateConversationCommand:
	conversation_id: UUID
	user_id: UUID
	created_at: datetime
