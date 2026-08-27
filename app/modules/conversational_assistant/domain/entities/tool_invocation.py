from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.modules.conversational_assistant.domain.exceptions import InvalidToolInvocationOutcome


@dataclass
class ToolInvocation:
	"""One tool call made by the agent during a Run -- the audit trail of that turn's tool use,
	the same shape TicketHistoryEntry gives Ticket's own lifecycle transitions.

	`arguments` is always the *validated*, Pydantic-parsed arguments the tool actually executed
	with, never the LLM's raw untrusted JSON. `result` is the narrowed payload actually handed
	back to the model -- already minimized by the tool itself, so cheap to store here too.
	"""

	id: UUID
	tool_name: str
	arguments: dict[str, Any]
	result: dict[str, Any] | None
	error: str | None
	started_at: datetime
	completed_at: datetime

	def __post_init__(self) -> None:
		if (self.result is None) == (self.error is None):
			raise InvalidToolInvocationOutcome(
				"A tool invocation must record exactly one of result or error."
			)

	@classmethod
	def succeeded(
		cls, *, id: UUID, tool_name: str, arguments: dict[str, Any], result: dict[str, Any],
		started_at: datetime, completed_at: datetime,
	) -> ToolInvocation:
		return cls(
			id=id, tool_name=tool_name, arguments=arguments, result=result, error=None,
			started_at=started_at, completed_at=completed_at,
		)

	@classmethod
	def failed(
		cls, *, id: UUID, tool_name: str, arguments: dict[str, Any], error: str,
		started_at: datetime, completed_at: datetime,
	) -> ToolInvocation:
		return cls(
			id=id, tool_name=tool_name, arguments=arguments, result=None, error=error,
			started_at=started_at, completed_at=completed_at,
		)
