from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class UserMessageReceived(DomainEvent):
	"""A human sent a message and an agent Run has started for it. Always carries a real
	actor_id (the sender) -- unlike the two outcome events below, this is the one moment in a
	Run's life at which an authenticated CurrentUser exists.
	"""

	conversation_id: UUID
	message_id: UUID
	run_id: UUID
