from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_jira_metrics.handler import GetJiraMetricsHandler
from app.modules.analytics.application.queries.get_jira_metrics.query import GetJiraMetricsQuery
from app.modules.analytics.application.security.access_scope import (
	READ_ANY_APPLICATION_PERMISSION as ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
)
from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_read_repository import (
	SqlAlchemyAnalyticsReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import compute_application_scope
from app.modules.ticket_management.domain.enums.application import Application


class GetJiraMetricsArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	application: Application | None = None
	time_range: TimeRange = TimeRange.LAST_30_DAYS


async def _execute(args: GetJiraMetricsArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		allowed_applications = compute_application_scope(
			ctx.current_user, ANALYTICS_READ_ANY_APPLICATION_PERMISSION, Application,
		)
		if (
			allowed_applications is not None
			and args.application is not None
			and args.application not in allowed_applications
		):
			return ToolResult(ok=False, error="Vous n'avez pas accès aux indicateurs de cette application.")

		applications = {args.application} if args.application is not None else allowed_applications
		handler = GetJiraMetricsHandler(SqlAlchemyAnalyticsReadRepository(session))
		metrics = await handler.handle(
			GetJiraMetricsQuery(
				time_range=args.time_range,
				applications=frozenset(applications) if applications is not None else None,
			)
		)
		return ToolResult(
			ok=True,
			payload={
				"requires_jira": metrics.requires_jira,
				"awaiting_delivery": metrics.awaiting_delivery,
				"avg_delivery_delay_days": metrics.avg_delivery_delay_days,
			},
		)
	finally:
		await session.close()


GET_JIRA_METRICS = ToolSpec(
	name="get_jira_metrics",
	description=(
		"Retourne la dépendance Jira sur une période : nombre de tickets nécessitant un ticket "
		"Jira, nombre encore en attente de date de livraison, et délai de livraison moyen en "
		"jours."
	),
	args_model=GetJiraMetricsArgs,
	required_permission="analytics.read",
	execute=_execute,
)
