from __future__ import annotations

from app.modules.conversational_assistant.application.dto.conversation_summary_dto import ConversationSummaryDTO
from app.modules.conversational_assistant.application.interfaces.conversation_read_repository import (
	ConversationReadRepository,
)
from app.modules.conversational_assistant.application.queries.list_conversations.query import (
	ListConversationsQuery,
)
from app.shared.pagination import Page


class ListConversationsHandler:
	def __init__(self, read_repository: ConversationReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: ListConversationsQuery) -> Page[ConversationSummaryDTO]:
		return await self.read_repository.list_conversations(query.user_id, limit=query.limit, offset=query.offset)
