from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class SendMessageResultDTO:
	conversation_id: UUID
	user_message_id: UUID
	run_id: UUID
