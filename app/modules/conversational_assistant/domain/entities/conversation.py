from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.modules.conversational_assistant.domain.entities.message import Message
from app.modules.conversational_assistant.domain.entities.run import Run
from app.modules.conversational_assistant.domain.entities.tool_invocation import ToolInvocation
from app.modules.conversational_assistant.domain.enums.message_role import MessageRole
from app.modules.conversational_assistant.domain.exceptions import RunNotFound

_TITLE_MAX_LENGTH = 60


def _summarize_title(content: str) -> str:
	collapsed = " ".join(content.split())
	if len(collapsed) <= _TITLE_MAX_LENGTH:
		return collapsed
	return collapsed[:_TITLE_MAX_LENGTH].rsplit(" ", 1)[0] + "…"


@dataclass
class Conversation:
	"""Aggregate root: one chat thread, owning its ordered Messages and Runs -- the same shape
	Ticket owns Comment/Attachment/TicketHistoryEntry. Ownership is strictly self-only in v1:
	`user_id` is the only thing an instance policy ever checks, with no breadth override.
	"""

	id: UUID
	user_id: UUID
	created_at: datetime
	updated_at: datetime
	title: str | None = None
	messages: list[Message] = field(default_factory=list)
	runs: list[Run] = field(default_factory=list)

	@classmethod
	def start(cls, *, id: UUID, user_id: UUID, created_at: datetime) -> Conversation:
		return cls(id=id, user_id=user_id, created_at=created_at, updated_at=created_at)

	def add_user_message(self, *, id: UUID, content: str, sent_at: datetime) -> Message:
		message = Message.create(id=id, role=MessageRole.USER, content=content, created_at=sent_at)
		self.messages.append(message)
		self.updated_at = sent_at
		return message

	def set_title_from_first_message(self, content: str) -> None:
		self.title = _summarize_title(content)

	def start_run(self, *, id: UUID, triggering_message_id: UUID, started_at: datetime) -> Run:
		run = Run.start(id=id, triggering_message_id=triggering_message_id, started_at=started_at)
		self.runs.append(run)
		return run

	def get_run(self, run_id: UUID) -> Run:
		for run in self.runs:
			if run.id == run_id:
				return run
		raise RunNotFound()

	def mark_run_running(self, *, run_id: UUID, at: datetime) -> None:
		self.get_run(run_id).mark_running(at=at)

	def complete_run(
		self, *, run_id: UUID, response_message_id: UUID, content: str,
		tool_invocations: Sequence[ToolInvocation], completed_at: datetime,
	) -> Message:
		run = self.get_run(run_id)
		message = Message.create(
			id=response_message_id, role=MessageRole.ASSISTANT, content=content, created_at=completed_at,
		)
		run.complete(
			response_message_id=response_message_id, tool_invocations=tool_invocations, completed_at=completed_at,
		)
		self.messages.append(message)
		self.updated_at = completed_at
		return message

	def fail_run(
		self, *, run_id: UUID, failure_reason: str, failure_detail: str | None, completed_at: datetime,
	) -> None:
		run = self.get_run(run_id)
		run.fail(failure_reason=failure_reason, failure_detail=failure_detail, completed_at=completed_at)
		self.updated_at = completed_at

	@property
	def latest_run(self) -> Run | None:
		return self.runs[-1] if self.runs else None
