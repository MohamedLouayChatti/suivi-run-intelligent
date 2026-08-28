from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_activity_trend.handler import GetActivityTrendHandler
from app.modules.analytics.application.queries.get_activity_trend.query import GetActivityTrendQuery
from app.modules.analytics.application.security.access_scope import (
	READ_ANY_APPLICATION_PERMISSION as ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
)
from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_read_repository import (
	SqlAlchemyAnalyticsReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import (
	APPLICATION_OUT_OF_SCOPE_ERROR,
	ApplicationOutOfScope,
	scoped_applications,
)
from app.modules.ticket_management.domain.enums.application import Application


class GetActivityTrendArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	application: Application | None = None
	time_range: TimeRange = TimeRange.LAST_3_MONTHS


async def _execute(args: GetActivityTrendArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		try:
			applications = scoped_applications(
				ctx.current_user, ANALYTICS_READ_ANY_APPLICATION_PERMISSION, Application, args.application,
			)
		except ApplicationOutOfScope:
			return ToolResult(ok=False, error=APPLICATION_OUT_OF_SCOPE_ERROR)

		handler = GetActivityTrendHandler(SqlAlchemyAnalyticsReadRepository(session))
		points = await handler.handle(
			GetActivityTrendQuery(time_range=args.time_range, applications=applications)
		)
		return ToolResult(
			ok=True,
			payload={
				"time_range": args.time_range.value,
				"scope": "toutes les applications" if applications is None else sorted(
					application.value for application in applications
				),
				# The bucket span varies with the range (a day for 30D, a week for 3M, a month
				# beyond), so each point carries its own start date rather than an index the model
				# would have to interpret against a scheme it cannot see.
				"points": [
					{
						"bucket_start": point.bucket_start.date().isoformat(),
						"created": point.created,
						"resolved": point.resolved,
					}
					for point in points
				],
			},
		)
	finally:
		await session.close()


GET_ACTIVITY_TREND = ToolSpec(
	name="get_activity_trend",
	description=(
		"Retourne l'évolution du nombre de tickets créés et résolus sur une période, pour une "
		"application donnée ou pour toutes celles que l'utilisateur peut consulter. Utile pour "
		"décrire une tendance (activité en hausse, en baisse, pics) plutôt qu'un total."
	),
	args_model=GetActivityTrendArgs,
	required_permission="analytics.read",
	execute=_execute,
)
