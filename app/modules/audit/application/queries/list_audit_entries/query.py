from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ListAuditEntriesQuery:
	module: str | None = None
	event_type: str | None = None
	resource_type: str | None = None
	actor_id: UUID | None = None
	date_from: datetime | None = None
	date_to: datetime | None = None
	limit: int = 100
	offset: int = 0
