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
from app.modules.analytics.application.security.access_scope import READ_ANY_APPLICATION_PERMISSION
from app.modules.analytics.domain.repositories.health_baseline_repository import HealthBaselineRepository
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_admin_analytics_read_repository import (
	SqlAlchemyAdminAnalyticsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_read_repository import (
	SqlAlchemyAnalyticsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_health_baseline_repository import (
	SqlAlchemyHealthBaselineRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_application_insights_read_repository import (
	SqlAlchemyApplicationInsightsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_personal_analytics_read_repository import (
	SqlAlchemyPersonalAnalyticsReadRepository,
)
from app.modules.auth.api.dependencies import get_user_read_repository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.domain.enums.application import Application
from app.shared.database.session import create_session
from app.shared.security.application_scope import require_application_scope


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


async def get_health_baseline_repository() -> AsyncIterator[SqlAlchemyHealthBaselineRepository]:
	session = create_session()
	try:
		yield SqlAlchemyHealthBaselineRepository(session)
	finally:
		await session.close()


# None means "every application" (the caller holds analytics.read_any_application), otherwise
# the caller's own assignments. The same shared dependency backs Ticket Management's
# list/search/export scope, so both modules answer "how wide may this caller look" identically
# instead of each re-deriving it -- see app/shared/security/application_scope.py.
require_analytics_applications_scope = require_application_scope(READ_ANY_APPLICATION_PERMISSION, Application)


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
	health_baselines: Annotated[HealthBaselineRepository, Depends(get_health_baseline_repository)],
) -> GetAdminOverviewHandler:
	return GetAdminOverviewHandler(repository, user_repository, health_baselines)


def get_my_kpi_snapshot_handler(
	repository: Annotated[SqlAlchemyPersonalAnalyticsReadRepository, Depends(get_personal_analytics_read_repository)],
) -> GetMyKpiSnapshotHandler:
	return GetMyKpiSnapshotHandler(repository)


def get_my_activity_trend_handler(
	repository: Annotated[SqlAlchemyPersonalAnalyticsReadRepository, Depends(get_personal_analytics_read_repository)],
) -> GetMyActivityTrendHandler:
	return GetMyActivityTrendHandler(repository)
