from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetSimilarIncidentsQuery:
	ticket_id: UUID
