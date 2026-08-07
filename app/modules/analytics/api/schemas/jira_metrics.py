from __future__ import annotations

from pydantic import BaseModel

from app.modules.analytics.application.dto.jira_metrics_dto import JiraMetricsDTO


class JiraMetricsResponse(BaseModel):
	requires_jira: int
	awaiting_delivery: int
	avg_delivery_delay_days: float

	@classmethod
	def from_dto(cls, metrics: JiraMetricsDTO) -> JiraMetricsResponse:
		return cls(
			requires_jira=metrics.requires_jira,
			awaiting_delivery=metrics.awaiting_delivery,
			avg_delivery_delay_days=metrics.avg_delivery_delay_days,
		)
