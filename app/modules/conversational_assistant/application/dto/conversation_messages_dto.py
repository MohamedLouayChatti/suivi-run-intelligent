from __future__ import annotations

from dataclasses import dataclass

from app.modules.conversational_assistant.application.dto.message_dto import MessageDTO
from app.modules.conversational_assistant.application.dto.run_summary_dto import RunSummaryDTO
from app.shared.pagination import Page


@dataclass(frozen=True)
class ConversationMessagesDTO:
	"""Result of GET /conversations/{id}/messages.

	`latest_run` is populated only when the most recent Run is *not* COMPLETED -- a completed
	run's answer is already the last item in `messages`, so repeating it would be redundant.
	Reconciliation reads this directly: PENDING/RUNNING means "show a live indicator and open
	the stream at this id", FAILED means "render an inline error", None means fully settled.
	"""

	messages: Page[MessageDTO]
	latest_run: RunSummaryDTO | None
