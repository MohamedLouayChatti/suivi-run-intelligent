from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.conversational_assistant.domain.enums.message_role import MessageRole
from app.modules.conversational_assistant.domain.exceptions import EmptyMessageContent


@dataclass
class Message:
	"""One chat bubble. Deliberately carries no status field: a row only ever exists once its
	content is final. A user message is written synchronously by the request that sent it; an
	assistant message is written only by a successfully-completed Run (see Run) -- never
	inserted pending and never updated afterwards. This is what makes "exclude failed turns
	from future LLM context" true by construction rather than a filter someone has to remember.
	"""

	id: UUID
	role: MessageRole
	content: str
	created_at: datetime

	@classmethod
	def create(cls, *, id: UUID, role: MessageRole, content: str, created_at: datetime) -> Message:
		if not content.strip():
			raise EmptyMessageContent()
		return cls(id=id, role=role, content=content, created_at=created_at)
