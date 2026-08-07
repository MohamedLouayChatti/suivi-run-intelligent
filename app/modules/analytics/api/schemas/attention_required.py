from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.modules.analytics.api.schemas.user_summary import AnalyticsUserSummaryResponse
from app.modules.analytics.application.dto.attention_required_dto import AgingIncidentDTO, AttentionRequiredDTO
from app.modules.ticket_management.domain.enums.priority import Priority


class AgingIncidentResponse(BaseModel):
	ticket_id: UUID
	title: str
	age_days: int
	priority: Priority
	assignee_id: UUID
	assignee: AnalyticsUserSummaryResponse | None

	@classmethod
	def from_dto(cls, incident: AgingIncidentDTO) -> AgingIncidentResponse:
		return cls(
			ticket_id=incident.ticket_id,
			title=incident.title,
			age_days=incident.age_days,
			priority=incident.priority,
			assignee_id=incident.assignee_id,
			assignee=AnalyticsUserSummaryResponse.from_dto(incident.assignee),
		)


class AttentionRequiredResponse(BaseModel):
	count: int
	threshold_days: int
	incidents: list[AgingIncidentResponse]

	@classmethod
	def from_dto(cls, data: AttentionRequiredDTO) -> AttentionRequiredResponse:
		return cls(
			count=data.count,
			threshold_days=data.threshold_days,
			incidents=[AgingIncidentResponse.from_dto(incident) for incident in data.incidents],
		)
