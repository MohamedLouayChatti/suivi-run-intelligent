from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_kpi_snapshot.handler import GetKpiSnapshotHandler
from app.modules.analytics.application.queries.get_kpi_snapshot.query import GetKpiSnapshotQuery
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


class GetKpiSnapshotArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	application: Application | None = None
	time_range: TimeRange = TimeRange.LAST_30_DAYS


async def _execute(args: GetKpiSnapshotArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		try:
			applications = scoped_applications(
				ctx.current_user, ANALYTICS_READ_ANY_APPLICATION_PERMISSION, Application, args.application,
			)
		except ApplicationOutOfScope:
			return ToolResult(ok=False, error=APPLICATION_OUT_OF_SCOPE_ERROR)

		handler = GetKpiSnapshotHandler(SqlAlchemyAnalyticsReadRepository(session))
		snapshot = await handler.handle(
			GetKpiSnapshotQuery(
				time_range=args.time_range,
				applications=applications,
			)
		)
		return ToolResult(
			ok=True,
			payload={
				"total_tickets": snapshot.total_tickets,
				"open_tickets": snapshot.open_tickets,
				"resolved_tickets": snapshot.resolved_tickets,
				"urgent_tickets": snapshot.urgent_tickets,
				"avg_resolution_hours": round(snapshot.avg_resolution_hours, 1),
			},
		)
	finally:
		await session.close()


GET_KPI_SNAPSHOT = ToolSpec(
	name="get_kpi_snapshot",
	description=(
		"Retourne les indicateurs clés (tickets totaux, ouverts, résolus, urgents, temps de "
		"résolution moyen) pour une application donnée ou pour les applications de l'utilisateur, "
		"sur une période donnée."
	),
	args_model=GetKpiSnapshotArgs,
	required_permission="analytics.read",
	execute=_execute,
)
