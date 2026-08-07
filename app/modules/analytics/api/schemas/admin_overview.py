from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.modules.analytics.api.schemas.user_summary import AnalyticsUserSummaryResponse
from app.modules.analytics.application.dto.admin_overview_dto import (
	AdminOverviewDTO, AppJiraDependencyDTO, AppMonthlyTrendPointDTO, AppResolutionTimeDTO,
	AppTransferRateDTO, AppWorkloadRowDTO, ApplicationHealthDTO, EngineerDatumDTO, HealthLevel, TeamOverviewDTO,
)
from app.modules.ticket_management.domain.enums.application import Application


class AppWorkloadRowResponse(BaseModel):
	application: Application
	open: int
	in_progress: int
	resolved: int

	@classmethod
	def from_dto(cls, row: AppWorkloadRowDTO) -> AppWorkloadRowResponse:
		return cls(application=row.application, open=row.open, in_progress=row.in_progress, resolved=row.resolved)


class ApplicationHealthResponse(BaseModel):
	application: Application
	health: HealthLevel
	active_tickets: int
	avg_resolution_hours: float
	urgent_tickets: int

	@classmethod
	def from_dto(cls, health: ApplicationHealthDTO) -> ApplicationHealthResponse:
		return cls(
			application=health.application,
			health=health.health,
			active_tickets=health.active_tickets,
			avg_resolution_hours=health.avg_resolution_hours,
			urgent_tickets=health.urgent_tickets,
		)


class AppResolutionTimeResponse(BaseModel):
	application: Application
	avg_resolution_hours: float

	@classmethod
	def from_dto(cls, row: AppResolutionTimeDTO) -> AppResolutionTimeResponse:
		return cls(application=row.application, avg_resolution_hours=row.avg_resolution_hours)


class AppJiraDependencyResponse(BaseModel):
	application: Application
	jira_incidents: int

	@classmethod
	def from_dto(cls, row: AppJiraDependencyDTO) -> AppJiraDependencyResponse:
		return cls(application=row.application, jira_incidents=row.jira_incidents)


class AppTransferRateResponse(BaseModel):
	application: Application
	transfer_rate_pct: float

	@classmethod
	def from_dto(cls, row: AppTransferRateDTO) -> AppTransferRateResponse:
		return cls(application=row.application, transfer_rate_pct=row.transfer_rate_pct)


class AppMonthlyTrendPointResponse(BaseModel):
	month: date
	counts: dict[Application, int]

	@classmethod
	def from_dto(cls, point: AppMonthlyTrendPointDTO) -> AppMonthlyTrendPointResponse:
		return cls(month=point.month, counts=point.counts)


class EngineerDatumResponse(BaseModel):
	engineer_id: UUID
	value: float
	engineer: AnalyticsUserSummaryResponse | None

	@classmethod
	def from_dto(cls, datum: EngineerDatumDTO) -> EngineerDatumResponse:
		return cls(engineer_id=datum.engineer_id, value=datum.value, engineer=AnalyticsUserSummaryResponse.from_dto(datum.engineer))


class TeamOverviewResponse(BaseModel):
	active_tickets: list[EngineerDatumResponse]
	resolved_tickets: list[EngineerDatumResponse]
	avg_resolution_hours: list[EngineerDatumResponse]
	assignment_distribution: list[EngineerDatumResponse]
	transfer_rate_pct: list[EngineerDatumResponse]

	@classmethod
	def from_dto(cls, team: TeamOverviewDTO) -> TeamOverviewResponse:
		return cls(
			active_tickets=[EngineerDatumResponse.from_dto(d) for d in team.active_tickets],
			resolved_tickets=[EngineerDatumResponse.from_dto(d) for d in team.resolved_tickets],
			avg_resolution_hours=[EngineerDatumResponse.from_dto(d) for d in team.avg_resolution_hours],
			assignment_distribution=[EngineerDatumResponse.from_dto(d) for d in team.assignment_distribution],
			transfer_rate_pct=[EngineerDatumResponse.from_dto(d) for d in team.transfer_rate_pct],
		)


class AdminOverviewResponse(BaseModel):
	workload: list[AppWorkloadRowResponse]
	health: list[ApplicationHealthResponse]
	resolution_time: list[AppResolutionTimeResponse]
	jira_dependency: list[AppJiraDependencyResponse]
	transfer_rate: list[AppTransferRateResponse]
	monthly_trends: list[AppMonthlyTrendPointResponse]
	team: TeamOverviewResponse

	@classmethod
	def from_dto(cls, overview: AdminOverviewDTO) -> AdminOverviewResponse:
		return cls(
			workload=[AppWorkloadRowResponse.from_dto(r) for r in overview.workload],
			health=[ApplicationHealthResponse.from_dto(r) for r in overview.health],
			resolution_time=[AppResolutionTimeResponse.from_dto(r) for r in overview.resolution_time],
			jira_dependency=[AppJiraDependencyResponse.from_dto(r) for r in overview.jira_dependency],
			transfer_rate=[AppTransferRateResponse.from_dto(r) for r in overview.transfer_rate],
			monthly_trends=[AppMonthlyTrendPointResponse.from_dto(r) for r in overview.monthly_trends],
			team=TeamOverviewResponse.from_dto(overview.team),
		)
