from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SendMessageCommand:
	conversation_id: UUID
	message_id: UUID
	run_id: UUID
	content: str
	sent_at: datetime
	actor_id: UUID
