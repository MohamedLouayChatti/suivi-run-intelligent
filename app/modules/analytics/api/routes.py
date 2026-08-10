from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.modules.analytics.api import dependencies as dep
from app.modules.analytics.api.schemas.activity_point import ActivityPointResponse
from app.modules.analytics.api.schemas.admin_overview import AdminOverviewResponse
from app.modules.analytics.api.schemas.application_insights import ApplicationInsightsResponse
from app.modules.analytics.api.schemas.attention_required import AttentionRequiredResponse
from app.modules.analytics.api.schemas.distributions import DistributionsResponse
from app.modules.analytics.api.schemas.jira_metrics import JiraMetricsResponse
from app.modules.analytics.api.schemas.kpi_snapshot import KpiSnapshotResponse
from app.modules.analytics.api.schemas.my_kpi_snapshot import MyKpiSnapshotResponse
from app.modules.analytics.application.queries.get_activity_trend.query import GetActivityTrendQuery
from app.modules.analytics.application.queries.get_admin_overview.query import GetAdminOverviewQuery
from app.modules.analytics.application.queries.get_application_insights.query import GetApplicationInsightsQuery
from app.modules.analytics.application.queries.get_attention_required.query import (
	DEFAULT_ATTENTION_THRESHOLD_DAYS, GetAttentionRequiredQuery,
)
from app.modules.analytics.application.queries.get_distributions.query import GetDistributionsQuery
from app.modules.analytics.application.queries.get_jira_metrics.query import GetJiraMetricsQuery
from app.modules.analytics.application.queries.get_kpi_snapshot.query import GetKpiSnapshotQuery
from app.modules.analytics.application.queries.get_my_activity_trend.query import GetMyActivityTrendQuery
from app.modules.analytics.application.queries.get_my_kpi_snapshot.query import GetMyKpiSnapshotQuery
from app.modules.analytics.application.support.filters import effective_applications
from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.ticket_management.domain.enums.application import Application
from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.permissions import require_permissions

router = APIRouter(prefix="/analytics", tags=["analytics"], dependencies=[Depends(require_permissions("analytics.read"))])

AllowedApplications = Annotated[frozenset[Application] | None, Depends(dep.require_analytics_applications_scope)]


@router.get("/kpi-snapshot", response_model=KpiSnapshotResponse)
async def get_kpi_snapshot(
	handler=Depends(dep.get_kpi_snapshot_handler),
	allowed_applications: AllowedApplications = None,
	application: Application | None = None,
	time_range: TimeRange = TimeRange.LAST_30_DAYS,
):
	query = GetKpiSnapshotQuery(time_range=time_range, applications=effective_applications(application, allowed_applications))
	return KpiSnapshotResponse.from_dto(await handler.handle(query))


@router.get("/activity-trend", response_model=list[ActivityPointResponse])
async def get_activity_trend(
	handler=Depends(dep.get_activity_trend_handler),
	allowed_applications: AllowedApplications = None,
	application: Application | None = None,
	time_range: TimeRange = TimeRange.LAST_30_DAYS,
):
	query = GetActivityTrendQuery(time_range=time_range, applications=effective_applications(application, allowed_applications))
	return [ActivityPointResponse.from_dto(point) for point in await handler.handle(query)]


@router.get("/distributions", response_model=DistributionsResponse)
async def get_distributions(
	handler=Depends(dep.get_distributions_handler),
	allowed_applications: AllowedApplications = None,
	application: Application | None = None,
	time_range: TimeRange = TimeRange.LAST_30_DAYS,
):
	query = GetDistributionsQuery(time_range=time_range, applications=effective_applications(application, allowed_applications))
	return DistributionsResponse.from_dto(await handler.handle(query))


@router.get("/jira-metrics", response_model=JiraMetricsResponse)
async def get_jira_metrics(
	handler=Depends(dep.get_jira_metrics_handler),
	allowed_applications: AllowedApplications = None,
	application: Application | None = None,
	time_range: TimeRange = TimeRange.LAST_30_DAYS,
):
	query = GetJiraMetricsQuery(time_range=time_range, applications=effective_applications(application, allowed_applications))
	return JiraMetricsResponse.from_dto(await handler.handle(query))


@router.get("/attention-required", response_model=AttentionRequiredResponse)
async def get_attention_required(
	handler=Depends(dep.get_attention_required_handler),
	allowed_applications: AllowedApplications = None,
	application: Application | None = None,
	threshold_days: int = DEFAULT_ATTENTION_THRESHOLD_DAYS,
):
	query = GetAttentionRequiredQuery(
		applications=effective_applications(application, allowed_applications), threshold_days=threshold_days
	)
	return AttentionRequiredResponse.from_dto(await handler.handle(query))


@router.get("/application-insights", response_model=ApplicationInsightsResponse)
async def get_application_insights(
	application: Application,
	handler=Depends(dep.get_application_insights_handler),
	allowed_applications: AllowedApplications = None,
	time_range: TimeRange = TimeRange.LAST_30_DAYS,
):
	if allowed_applications is not None and application not in allowed_applications:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view insights for this application.")
	query = GetApplicationInsightsQuery(application=application, time_range=time_range)
	return ApplicationInsightsResponse.from_dto(await handler.handle(query))


@router.get(
	"/admin-overview",
	response_model=AdminOverviewResponse,
	dependencies=[Depends(require_permissions("analytics.read_any_application"))],
)
async def get_admin_overview(handler=Depends(dep.get_admin_overview_handler), time_range: TimeRange = TimeRange.LAST_30_DAYS):
	"""The cross-application "all applications" view, never scoped to a single application
	-- see AdminOverviewDTO. Gated by analytics.read_any_application, the same breadth
	permission that lets the other endpoints span every application."""
	query = GetAdminOverviewQuery(time_range=time_range)
	return AdminOverviewResponse.from_dto(await handler.handle(query))


@router.get("/my-kpi-snapshot", response_model=MyKpiSnapshotResponse)
async def get_my_kpi_snapshot(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_my_kpi_snapshot_handler),
):
	"""Dashboard-only personal KPIs (resolved/created this week, avg resolution time),
	scoped to the caller as assignee -- never application-scoped, since an assignee's own
	tickets are visible to them regardless of their current application assignments
	(same precedent as TicketAccessPolicy's assignee-only operations). No `application`/
	`time_range` params: this endpoint always answers "my last 7 days"."""
	return MyKpiSnapshotResponse.from_dto(await handler.handle(GetMyKpiSnapshotQuery(assignee_id=current_user.id)))


@router.get("/my-activity-trend", response_model=list[ActivityPointResponse])
async def get_my_activity_trend(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_my_activity_trend_handler),
):
	"""Dashboard-only: the caller's own created-vs-resolved trend, always the trailing
	30 days (no time-range selector on that page)."""
	points = await handler.handle(GetMyActivityTrendQuery(assignee_id=current_user.id))
	return [ActivityPointResponse.from_dto(point) for point in points]
