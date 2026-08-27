from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.conversational_assistant.application.dto.conversation_messages_dto import ConversationMessagesDTO
from app.modules.conversational_assistant.application.dto.conversation_summary_dto import ConversationSummaryDTO
from app.modules.conversational_assistant.application.dto.run_replay_dto import RunReplayDTO
from app.shared.pagination import Page


class ConversationReadRepository(ABC):
	@abstractmethod
	async def get_owner(self, conversation_id: UUID) -> UUID | None:
		"""The conversation's user_id, or None if no such conversation exists."""
		raise NotImplementedError

	@abstractmethod
	async def get_run_owner(self, run_id: UUID) -> UUID | None:
		"""The user_id of the conversation that owns this run, or None if no such run exists."""
		raise NotImplementedError

	@abstractmethod
	async def get_run_replay(self, run_id: UUID) -> RunReplayDTO | None:
		"""This run's current status and, once it has completed, the message it produced. None
		when no such run exists. Read by the SSE route so a client that connects after the run
		already resolved is answered from stored state instead of waiting forever."""
		raise NotImplementedError

	@abstractmethod
	async def get_messages(
		self, conversation_id: UUID, *, limit: int, offset: int
	) -> ConversationMessagesDTO | None:
		"""None when no conversation with this id exists."""
		raise NotImplementedError

	@abstractmethod
	async def list_conversations(self, user_id: UUID, *, limit: int, offset: int) -> Page[ConversationSummaryDTO]:
		raise NotImplementedError
