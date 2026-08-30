from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
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


class SimilarityAnalysisStatus(StrEnum):
	"""Whether this ticket's similarity analysis has run yet.

	Exists because an empty result has two meanings that a bare list cannot tell apart, and they
	are opposite ones: "nothing in the corpus is close enough to this description" is a finding,
	while "we have not looked yet" is not. Since a newly created ticket is analysed in a background
	job rather than in the request that created it, the second case is now an ordinary state a
	reader can arrive in, lasting as long as the job takes.

	A read-model concept rather than a domain one, which is why it lives here beside the DTO it is
	returned on and not in domain/enums/. Nothing persists it and no rule branches on it: it is
	derived per request from whether the corpus holds this ticket, and it exists so the frontend can
	say "analyse en cours" instead of asserting there are no similar incidents.
	"""

	PENDING = "PENDING"
	READY = "READY"


@dataclass(frozen=True)
class SimilarIncidentsDTO:
	"""The full answer to GET /knowledge-base/tickets/{ticket_id}/similar: the incidents, plus
	whether the analysis behind them has actually happened.

	An envelope rather than a bare list because the two fields are only meaningful together --
	`incidents` is always empty when `status` is PENDING, and reading either alone reproduces the
	ambiguity this type was added to remove.
	"""

	status: SimilarityAnalysisStatus
	incidents: list[SimilarIncidentDTO]
