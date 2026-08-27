from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class AgentRunFailed(DomainEvent):
	"""A background job could not complete a Run. actor_id is always None, same reasoning as
	AgentRunCompleted. Carries only the short, user-safe failure_reason -- never the full
	exception detail, which stays in the Run row for debugging and is never published.
	"""

	conversation_id: UUID
	run_id: UUID
	failure_reason: str
