from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.modules.analytics.application.queries.get_activity_trend.handler import GetActivityTrendHandler
from app.modules.analytics.application.queries.get_admin_overview.handler import GetAdminOverviewHandler
from app.modules.analytics.application.queries.get_application_insights.handler import GetApplicationInsightsHandler
from app.modules.analytics.application.queries.get_attention_required.handler import GetAttentionRequiredHandler
from app.modules.analytics.application.queries.get_distributions.handler import GetDistributionsHandler
from app.modules.analytics.application.queries.get_jira_metrics.handler import GetJiraMetricsHandler
from app.modules.analytics.application.queries.get_kpi_snapshot.handler import GetKpiSnapshotHandler
from app.modules.analytics.application.queries.get_my_activity_trend.handler import GetMyActivityTrendHandler
from app.modules.analytics.application.queries.get_my_kpi_snapshot.handler import GetMyKpiSnapshotHandler
from app.modules.analytics.application.security.access_scope import accessible_applications
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_admin_analytics_read_repository import (
	SqlAlchemyAdminAnalyticsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_read_repository import (
	SqlAlchemyAnalyticsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_application_insights_read_repository import (
	SqlAlchemyApplicationInsightsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_personal_analytics_read_repository import (
	SqlAlchemyPersonalAnalyticsReadRepository,
)
from app.modules.auth.api.dependencies import get_user_read_repository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.security.support import ADMIN_ROLE_NAME
from app.modules.ticket_management.domain.enums.application import Application
from app.shared.database.session import create_session
from app.shared.security.current_user import CurrentUser, get_current_user


async def get_analytics_read_repository() -> AsyncIterator[SqlAlchemyAnalyticsReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyAnalyticsReadRepository(session)
	finally:
		await session.close()


async def get_admin_analytics_read_repository() -> AsyncIterator[SqlAlchemyAdminAnalyticsReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyAdminAnalyticsReadRepository(session)
	finally:
		await session.close()


async def get_application_insights_read_repository() -> AsyncIterator[SqlAlchemyApplicationInsightsReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyApplicationInsightsReadRepository(session)
	finally:
		await session.close()


async def get_personal_analytics_read_repository() -> AsyncIterator[SqlAlchemyPersonalAnalyticsReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyPersonalAnalyticsReadRepository(session)
	finally:
		await session.close()


async def require_analytics_applications_scope(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	user_repository: Annotated[UserReadRepository, Depends(get_user_read_repository)],
) -> frozenset[Application] | None:
	"""None for admins (no restriction, may request "all applications"). Everyone else is
	silently scoped to their own assignments -- mirrors
	TicketAccessPolicy.allowed_applications_filter. Combined with an explicit `application`
	filter (if any) at the query layer, so an out-of-scope request simply yields an empty
	result rather than a 403 -- same behavior as Ticket Management's list/search endpoints.
	"""
	roles = await user_repository.get_user_roles(current_user.id)
	if any(role.name == ADMIN_ROLE_NAME for role in roles):
		return None
	return accessible_applications(current_user)


def get_kpi_snapshot_handler(
	repository: Annotated[SqlAlchemyAnalyticsReadRepository, Depends(get_analytics_read_repository)],
) -> GetKpiSnapshotHandler:
	return GetKpiSnapshotHandler(repository)


def get_activity_trend_handler(
	repository: Annotated[SqlAlchemyAnalyticsReadRepository, Depends(get_analytics_read_repository)],
) -> GetActivityTrendHandler:
	return GetActivityTrendHandler(repository)


def get_distributions_handler(
	repository: Annotated[SqlAlchemyAnalyticsReadRepository, Depends(get_analytics_read_repository)],
) -> GetDistributionsHandler:
	return GetDistributionsHandler(repository)


def get_jira_metrics_handler(
	repository: Annotated[SqlAlchemyAnalyticsReadRepository, Depends(get_analytics_read_repository)],
) -> GetJiraMetricsHandler:
	return GetJiraMetricsHandler(repository)


def get_attention_required_handler(
	repository: Annotated[SqlAlchemyAnalyticsReadRepository, Depends(get_analytics_read_repository)],
	user_repository: Annotated[UserReadRepository, Depends(get_user_read_repository)],
) -> GetAttentionRequiredHandler:
	return GetAttentionRequiredHandler(repository, user_repository)


def get_application_insights_handler(
	repository: Annotated[SqlAlchemyApplicationInsightsReadRepository, Depends(get_application_insights_read_repository)],
) -> GetApplicationInsightsHandler:
	return GetApplicationInsightsHandler(repository)


def get_admin_overview_handler(
	repository: Annotated[SqlAlchemyAdminAnalyticsReadRepository, Depends(get_admin_analytics_read_repository)],
	user_repository: Annotated[UserReadRepository, Depends(get_user_read_repository)],
) -> GetAdminOverviewHandler:
	return GetAdminOverviewHandler(repository, user_repository)


def get_my_kpi_snapshot_handler(
	repository: Annotated[SqlAlchemyPersonalAnalyticsReadRepository, Depends(get_personal_analytics_read_repository)],
) -> GetMyKpiSnapshotHandler:
	return GetMyKpiSnapshotHandler(repository)


def get_my_activity_trend_handler(
	repository: Annotated[SqlAlchemyPersonalAnalyticsReadRepository, Depends(get_personal_analytics_read_repository)],
) -> GetMyActivityTrendHandler:
	return GetMyActivityTrendHandler(repository)
