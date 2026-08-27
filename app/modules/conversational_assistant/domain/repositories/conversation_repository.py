from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.conversation import Conversation


class ConversationRepository(ABC):
	@abstractmethod
	async def add(self, conversation: Conversation) -> None:
		raise NotImplementedError

	@abstractmethod
	async def get(self, conversation_id: UUID) -> Conversation | None:
		raise NotImplementedError

	@abstractmethod
	async def save(self, conversation: Conversation) -> None:
		raise NotImplementedError
