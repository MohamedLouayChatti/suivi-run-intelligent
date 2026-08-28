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

# The two statuses a caller can still act on by reconnecting. A COMPLETED run's answer is already
# the last item in `messages`, and a FAILED one is reported through `failed_runs` at the position
# it occurred, so neither needs repeating as `latest_run`.
_IN_FLIGHT_STATUSES = (RunStatus.PENDING, RunStatus.RUNNING)


class GetConversationMessagesHandler:
	def __init__(self, read_repository: ConversationReadRepository) -> None:
		self.read_repository = read_repository

	async def handle(self, query: GetConversationMessagesQuery) -> ConversationMessagesDTO:
		result = await self.read_repository.get_messages(
			query.conversation_id, limit=query.limit, offset=query.offset,
		)
		if result is None:
			raise ConversationNotFound()
		if result.latest_run is not None and result.latest_run.status not in _IN_FLIGHT_STATUSES:
			return ConversationMessagesDTO(
				messages=result.messages, latest_run=None, failed_runs=result.failed_runs,
			)
		return result
