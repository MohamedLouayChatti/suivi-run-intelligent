from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO
from app.modules.analytics.application.dto.attention_required_dto import AttentionRequiredDTO
from app.modules.analytics.application.dto.distributions_dto import DistributionsDTO
from app.modules.analytics.application.dto.jira_metrics_dto import JiraMetricsDTO
from app.modules.analytics.application.dto.kpi_snapshot_dto import KpiTotalsDTO
from app.modules.analytics.application.dto.resolution_ranking_dto import ResolutionRankingDTO
from app.modules.analytics.application.support.time_range import DateWindow, TimeRange
from app.modules.ticket_management.domain.enums.application import Application


class AnalyticsReadRepository(ABC):
	"""Backs the core operational widgets: KPI snapshot, activity trend, status/category/
	priority distributions, Jira metrics, attention-required. Every method is scoped to
	`applications` (None = no restriction, i.e. admin viewing "all")."""

	@abstractmethod
	async def get_kpi_totals(self, applications: frozenset[Application] | None, window: DateWindow) -> KpiTotalsDTO:
		raise NotImplementedError

	@abstractmethod
	async def get_activity_trend(
		self, applications: frozenset[Application] | None, time_range: TimeRange
	) -> list[ActivityPointDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_distributions(self, applications: frozenset[Application] | None, window: DateWindow) -> DistributionsDTO:
		raise NotImplementedError

	@abstractmethod
	async def get_jira_metrics(self, applications: frozenset[Application] | None, window: DateWindow) -> JiraMetricsDTO:
		raise NotImplementedError

	@abstractmethod
	async def get_attention_required(
		self, applications: frozenset[Application] | None, threshold_days: int
	) -> AttentionRequiredDTO:
		raise NotImplementedError

	@abstractmethod
	async def get_resolution_ranking(
		self,
		*,
		applications: frozenset[Application] | None,
		window: DateWindow | None,
		assignee_id: UUID | None,
		slowest_first: bool,
		limit: int,
	) -> ResolutionRankingDTO:
		"""Resolved tickets ordered by how long they took. `window` is optional and applies to
		`resolved_at`; None ranks over all history, which is what "the ticket that took longest"
		usually means. Keyword-only, unlike its neighbours, because five parameters of which
		three are optional read as noise positionally."""
		raise NotImplementedError
