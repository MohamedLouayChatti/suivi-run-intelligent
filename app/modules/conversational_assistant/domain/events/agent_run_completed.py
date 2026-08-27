from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class AgentRunCompleted(DomainEvent):
	"""A background job finished a Run successfully. actor_id is always None -- nothing
	authenticated exists inside the background job that publishes this, the same precedent as
	Knowledge Base's SimilarityGraphRecalculated.
	"""

	conversation_id: UUID
	run_id: UUID
	response_message_id: UUID
	tool_call_count: int
