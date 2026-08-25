from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.ticket_management.domain.enums.status import Status


@dataclass(frozen=True)
class SimilarIncidentDTO:
	"""Final shape returned by GET /knowledge-base/tickets/{ticket_id}/similar -- a persisted
	SimilarityResultRowDTO merged with live ticket context from Ticket Management. Matches the
	frontend's existing similar-incidents-card.tsx mock shape (id/title/status/similarity), plus
	resolution_notes.
	"""

	ticket_id: UUID
	title: str
	status: Status
	resolution_notes: str | None
	similarity_score: float
	rank: int
	matched_reference: bool
