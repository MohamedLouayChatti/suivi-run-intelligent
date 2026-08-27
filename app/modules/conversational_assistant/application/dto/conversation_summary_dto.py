from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.conversation import Conversation


@dataclass(frozen=True)
class ConversationSummaryDTO:
	id: UUID
	title: str | None
	created_at: datetime
	updated_at: datetime

	@classmethod
	def from_conversation(cls, conversation: Conversation) -> ConversationSummaryDTO:
		return cls(
			id=conversation.id, title=conversation.title,
			created_at=conversation.created_at, updated_at=conversation.updated_at,
		)
