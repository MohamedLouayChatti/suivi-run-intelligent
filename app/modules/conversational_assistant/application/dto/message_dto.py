from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.message import Message
from app.modules.conversational_assistant.domain.enums.message_role import MessageRole


@dataclass(frozen=True)
class MessageDTO:
	id: UUID
	role: MessageRole
	content: str
	created_at: datetime

	@classmethod
	def from_message(cls, message: Message) -> MessageDTO:
		return cls(id=message.id, role=message.role, content=message.content, created_at=message.created_at)
