from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.conversational_assistant.application.dto.message_dto import MessageDTO
from app.modules.conversational_assistant.domain.enums.run_status import RunStatus

_TERMINAL_STATUSES = frozenset({RunStatus.COMPLETED, RunStatus.FAILED})


@dataclass(frozen=True)
class RunReplayDTO:
	"""A run's settled outcome, read from the database rather than from the live stream.

	This is what a client that opened the stream *after* the run had already resolved needs: the
	connection manager buffers nothing, so without this the client would wait on a terminal event
	that was published to an empty subscriber list and will never be sent again.
	"""

	run_id: UUID
	status: RunStatus
	failure_reason: str | None
	response_message: MessageDTO | None

	@property
	def is_terminal(self) -> bool:
		return self.status in _TERMINAL_STATUSES
