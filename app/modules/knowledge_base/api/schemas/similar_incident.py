from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.modules.knowledge_base.application.dto.similar_incident_dto import SimilarIncidentDTO
from app.modules.ticket_management.domain.enums.status import Status


class SimilarIncidentResponse(BaseModel):

	ticket_id: UUID
	title: str
	status: Status
	resolution_notes: str | None
	similarity_score: float
	rank: int
	matched_reference: bool

	@classmethod
	def from_dto(cls, incident: SimilarIncidentDTO) -> SimilarIncidentResponse:
		return cls(
			ticket_id=incident.ticket_id,
			title=incident.title,
			status=incident.status,
			resolution_notes=incident.resolution_notes,
			similarity_score=incident.similarity_score,
			rank=incident.rank,
			matched_reference=incident.matched_reference,
		)
