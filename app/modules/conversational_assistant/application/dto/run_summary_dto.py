from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.run import Run
from app.modules.conversational_assistant.domain.enums.run_status import RunStatus


@dataclass(frozen=True)
class RunSummaryDTO:
	id: UUID
	status: RunStatus
	failure_reason: str | None
	created_at: datetime
	# Which user message this run was answering. Carried so a failed run can be replayed at the
	# position it actually occupies in the transcript rather than appended to the end -- a failure
	# that reads as a reply to the wrong question is barely better than no failure at all.
	triggering_message_id: UUID

	@classmethod
	def from_run(cls, run: Run) -> RunSummaryDTO:
		return cls(
			id=run.id, status=run.status, failure_reason=run.failure_reason,
			created_at=run.started_at, triggering_message_id=run.triggering_message_id,
		)
