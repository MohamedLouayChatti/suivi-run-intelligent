from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AuditEntry:
	id: UUID
	occurred_at: datetime
	module: str
	event_type: str
	action: str
	resource_type: str | None
	actor_id: UUID | None
	payload: dict[str, Any] = field(default_factory=dict)

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		occurred_at: datetime,
		module: str,
		event_type: str,
		action: str,
		resource_type: str | None,
		actor_id: UUID | None,
		payload: dict[str, Any],
	) -> AuditEntry:
		return cls(
			id=id,
			occurred_at=occurred_at,
			module=module,
			event_type=event_type,
			action=action,
			resource_type=resource_type,
			actor_id=actor_id,
			payload=payload,
		)
