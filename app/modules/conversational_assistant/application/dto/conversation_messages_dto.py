from __future__ import annotations

from dataclasses import dataclass

from app.modules.conversational_assistant.application.dto.message_dto import MessageDTO
from app.modules.conversational_assistant.application.dto.run_summary_dto import RunSummaryDTO
from app.shared.pagination import Page


@dataclass(frozen=True)
class ConversationMessagesDTO:
	"""Result of GET /conversations/{id}/messages.

	`latest_run` is populated only while the most recent Run is still *in flight* -- PENDING or
	RUNNING -- and means "show a live indicator and open the stream at this id". A completed run's
	answer is already the last item in `messages`, and a failed one is reported through
	`failed_runs` instead, so `None` here means there is nothing left to reconnect to.

	`failed_runs` is every Run of this conversation that failed, not merely the last one. A run
	produces no Message, so a failure used to exist only as long as it happened to be the latest
	run: send one more message afterwards and the transcript closed over it, leaving two user
	messages back to back with nothing between them and no sign anything had gone wrong. Each
	entry names its `triggering_message_id` so the reader sees the failure against the question
	that provoked it. These stay out of `messages` deliberately -- a failure is not something the
	assistant said, and folding it in would feed the agent's own past failures back to it as
	conversation history on every later turn.
	"""

	messages: Page[MessageDTO]
	latest_run: RunSummaryDTO | None
	failed_runs: list[RunSummaryDTO]
