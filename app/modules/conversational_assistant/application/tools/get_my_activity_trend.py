from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_my_activity_trend.handler import GetMyActivityTrendHandler
from app.modules.analytics.application.queries.get_my_activity_trend.query import GetMyActivityTrendQuery
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_personal_analytics_read_repository import (
	SqlAlchemyPersonalAnalyticsReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec


class GetMyActivityTrendArgs(BaseModel):
	"""No fields: self-scoped to the caller as assignee, over a fixed trailing 30-day window --
	same as GET /analytics/my-activity-trend."""

	model_config = ConfigDict(extra="forbid")


async def _execute(args: GetMyActivityTrendArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		handler = GetMyActivityTrendHandler(SqlAlchemyPersonalAnalyticsReadRepository(session))
		points = await handler.handle(GetMyActivityTrendQuery(assignee_id=ctx.current_user.id))
		return ToolResult(
			ok=True,
			payload={
				"daily_activity": [
					{
						"date": point.bucket_start.date().isoformat(),
						"created": point.created,
						"resolved": point.resolved,
					}
					for point in points
				]
			},
		)
	finally:
		await session.close()


GET_MY_ACTIVITY_TREND = ToolSpec(
	name="get_my_activity_trend",
	description=(
		"Retourne l'évolution quotidienne des tickets créés et résolus par l'utilisateur sur "
		"les 30 derniers jours."
	),
	args_model=GetMyActivityTrendArgs,
	required_permission="analytics.read",
	execute=_execute,
)
