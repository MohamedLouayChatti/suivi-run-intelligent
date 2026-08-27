from __future__ import annotations

from app.modules.conversational_assistant.application.dto.conversation_messages_dto import ConversationMessagesDTO
from app.modules.conversational_assistant.application.exceptions import ConversationNotFound
from app.modules.conversational_assistant.application.interfaces.conversation_read_repository import (
	ConversationReadRepository,
)
from app.modules.conversational_assistant.application.queries.get_conversation_messages.query import (
	GetConversationMessagesQuery,
)
from app.modules.conversational_assistant.domain.enums.run_status import RunStatus


class GetConversationMessagesHandler:
	def __init__(self, read_repository: ConversationReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetConversationMessagesQuery) -> ConversationMessagesDTO:
		result = await self.read_repository.get_messages(
			query.conversation_id, limit=query.limit, offset=query.offset,
		)
		if result is None:
			raise ConversationNotFound()
		# A completed run's answer is already the last item in `messages` -- repeating it as
		# `latest_run` would be redundant. Reconciliation only needs this for the non-settled cases.
		if result.latest_run is not None and result.latest_run.status is RunStatus.COMPLETED:
			return ConversationMessagesDTO(messages=result.messages, latest_run=None)
		return result
