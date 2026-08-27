from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.modules.analytics.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.ticket_management.domain.enums.application import Application

# Re-exported rather than imported at each call site: HealthLevel moved to Domain once tiering
# became a domain service, and this DTO module was already every downstream caller's import
# path for it (api/schemas/admin_overview.py included), so re-exporting here means nothing
# downstream had to change.
from app.modules.analytics.domain.enums.health_level import HealthLevel

__all__ = [
	"AdminOverviewDTO", "AppJiraDependencyDTO", "AppMonthlyTrendPointDTO", "AppResolutionTimeDTO",
	"AppTransferRateDTO", "AppWorkloadRowDTO", "ApplicationHealthDTO", "EngineerDatumDTO",
	"HealthLevel", "TeamOverviewDTO",
]


@dataclass(frozen=True)
class AppWorkloadRowDTO:
	application: Application
	open: int
	in_progress: int
	resolved: int


@dataclass(frozen=True)
class ApplicationHealthDTO:
	application: Application
	health: HealthLevel
	active_tickets: int
	avg_resolution_hours: float
	urgent_tickets: int


@dataclass(frozen=True)
class AppResolutionTimeDTO:
	application: Application
	avg_resolution_hours: float


@dataclass(frozen=True)
class AppJiraDependencyDTO:
	application: Application
	jira_incidents: int


@dataclass(frozen=True)
class AppTransferRateDTO:
	application: Application
	transfer_rate_pct: float


@dataclass(frozen=True)
class AppMonthlyTrendPointDTO:
	month: date
	counts: dict[Application, int]


@dataclass(frozen=True)
class EngineerDatumDTO:
	engineer_id: UUID
	value: float
	engineer: UserSummaryDTO | None = None


@dataclass(frozen=True)
class TeamOverviewDTO:
	active_tickets: list[EngineerDatumDTO]
	resolved_tickets: list[EngineerDatumDTO]
	avg_resolution_hours: list[EngineerDatumDTO]
	assignment_distribution: list[EngineerDatumDTO]
	transfer_rate_pct: list[EngineerDatumDTO]


@dataclass(frozen=True)
class AdminOverviewDTO:
	"""Admin-only, "all applications" cross-cutting view -- backs the Cross Application
	Overview + Team Overview sections, which only ever render together."""

	workload: list[AppWorkloadRowDTO]
	health: list[ApplicationHealthDTO]
	resolution_time: list[AppResolutionTimeDTO]
	jira_dependency: list[AppJiraDependencyDTO]
	transfer_rate: list[AppTransferRateDTO]
	monthly_trends: list[AppMonthlyTrendPointDTO]
	team: TeamOverviewDTO
