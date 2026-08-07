from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.analytics.application.dto.admin_overview_dto import (
	AppJiraDependencyDTO, AppMonthlyTrendPointDTO, AppResolutionTimeDTO, AppTransferRateDTO,
	AppWorkloadRowDTO, ApplicationHealthDTO, TeamOverviewDTO,
)
from app.modules.analytics.application.support.time_range import DateWindow


class AdminAnalyticsReadRepository(ABC):
	"""Backs the admin-only, "all applications" Cross Application Overview + Team
	Overview sections. Never scoped by `applications` -- callers must already be
	authorized for the unrestricted view before reaching this repository."""

	@abstractmethod
	async def get_workload(self, window: DateWindow) -> list[AppWorkloadRowDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_health(self, window: DateWindow) -> list[ApplicationHealthDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_resolution_time_comparison(self, window: DateWindow) -> list[AppResolutionTimeDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_jira_dependency(self, window: DateWindow) -> list[AppJiraDependencyDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_transfer_rate(self, window: DateWindow) -> list[AppTransferRateDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_monthly_trends(self) -> list[AppMonthlyTrendPointDTO]:
		"""Always the trailing 12 calendar months -- ignores the selected time range,
		same as the frontend's mock generator."""
		raise NotImplementedError

	@abstractmethod
	async def get_team_overview(self, window: DateWindow) -> TeamOverviewDTO:
		raise NotImplementedError
