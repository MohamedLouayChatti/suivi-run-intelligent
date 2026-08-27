from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_my_kpi_snapshot.handler import GetMyKpiSnapshotHandler
from app.modules.analytics.application.queries.get_my_kpi_snapshot.query import GetMyKpiSnapshotQuery
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_personal_analytics_read_repository import (
	SqlAlchemyPersonalAnalyticsReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec


class GetMyKpiSnapshotArgs(BaseModel):
	"""No fields: this tool is always scoped to the caller as assignee, never a chosen user --
	the same self-scoping GET /analytics/my-kpi-snapshot itself uses."""

	model_config = ConfigDict(extra="forbid")


async def _execute(args: GetMyKpiSnapshotArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		handler = GetMyKpiSnapshotHandler(SqlAlchemyPersonalAnalyticsReadRepository(session))
		snapshot = await handler.handle(GetMyKpiSnapshotQuery(assignee_id=ctx.current_user.id))
		return ToolResult(
			ok=True,
			payload={
				"resolved_this_week": snapshot.resolved_this_week,
				"created_this_week": snapshot.created_this_week,
				"avg_resolution_hours": round(snapshot.avg_resolution_hours, 1),
			},
		)
	finally:
		await session.close()


GET_MY_KPI_SNAPSHOT = ToolSpec(
	name="get_my_kpi_snapshot",
	description=(
		"Retourne les indicateurs personnels de l'utilisateur pour les 7 derniers jours : "
		"tickets résolus, tickets créés, temps de résolution moyen."
	),
	args_model=GetMyKpiSnapshotArgs,
	required_permission="analytics.read",
	execute=_execute,
)
