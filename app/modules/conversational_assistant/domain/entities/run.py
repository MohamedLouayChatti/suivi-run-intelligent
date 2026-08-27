from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.tool_invocation import ToolInvocation
from app.modules.conversational_assistant.domain.enums.run_status import RunStatus
from app.modules.conversational_assistant.domain.exceptions import RunNotPending, RunNotRunning


@dataclass
class Run:
	"""One assistant turn: the agent's attempt to answer the Message that triggered it.

	Carries all in-flight/failure state so Message can stay free of orchestration concepts --
	PENDING/RUNNING never leak into what the UI renders as a chat bubble. `failure_reason` is
	short and user-safe (shown in the UI); `failure_detail` is for debugging only and is never
	returned to the end user.
	"""

	id: UUID
	triggering_message_id: UUID
	status: RunStatus
	started_at: datetime
	response_message_id: UUID | None = None
	completed_at: datetime | None = None
	failure_reason: str | None = None
	failure_detail: str | None = None
	tool_invocations: list[ToolInvocation] = field(default_factory=list)

	@classmethod
	def start(cls, *, id: UUID, triggering_message_id: UUID, started_at: datetime) -> Run:
		return cls(
			id=id, triggering_message_id=triggering_message_id,
			status=RunStatus.PENDING, started_at=started_at,
		)

	def mark_running(self, *, at: datetime) -> None:
		if self.status is not RunStatus.PENDING:
			raise RunNotPending()
		self.status = RunStatus.RUNNING

	def complete(
		self, *, response_message_id: UUID, tool_invocations: Sequence[ToolInvocation], completed_at: datetime,
	) -> None:
		if self.status is not RunStatus.RUNNING:
			raise RunNotRunning()
		self.status = RunStatus.COMPLETED
		self.response_message_id = response_message_id
		self.tool_invocations = list(tool_invocations)
		self.completed_at = completed_at

	def fail(self, *, failure_reason: str, failure_detail: str | None, completed_at: datetime) -> None:
		# Allowed from PENDING too: a failure can strike before mark_running's own commit lands
		# (e.g. the job never got that far), and the run must still be recordable as failed rather
		# than stuck.
		if self.status not in (RunStatus.PENDING, RunStatus.RUNNING):
			raise RunNotRunning()
		self.status = RunStatus.FAILED
		self.failure_reason = failure_reason
		self.failure_detail = failure_detail
		self.completed_at = completed_at
