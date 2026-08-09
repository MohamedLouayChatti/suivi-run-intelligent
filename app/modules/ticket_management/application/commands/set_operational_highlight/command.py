from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class SetOperationalHighlightCommand:
	ticket_id: UUID
	operational_highlight: bool
	updated_at: datetime
	actor_id: UUID
