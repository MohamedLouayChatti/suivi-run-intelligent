from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.exceptions import UnsupportedInsightsApplication
from app.modules.analytics.application.queries.get_application_insights.handler import (
	GetApplicationInsightsHandler,
)
from app.modules.analytics.application.queries.get_application_insights.query import (
	GetApplicationInsightsQuery,
)
from app.modules.analytics.application.security.access_scope import (
	READ_ANY_APPLICATION_PERMISSION as ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
)
from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_application_insights_read_repository import (
	SqlAlchemyApplicationInsightsReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import (
	APPLICATION_OUT_OF_SCOPE_ERROR,
	ApplicationOutOfScope,
	scoped_applications,
)
from app.modules.ticket_management.domain.enums.application import Application


class GetApplicationInsightsArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	# Required, unlike every other analytics tool: each application's insight is a different
	# shape entirely (a two-dimensional heatmap, a ranking, per-sub-application rows), so there
	# is nothing coherent to return for "all of them".
	application: Application
	time_range: TimeRange = TimeRange.LAST_3_MONTHS


async def _execute(args: GetApplicationInsightsArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		try:
			scoped_applications(
				ctx.current_user, ANALYTICS_READ_ANY_APPLICATION_PERMISSION, Application, args.application,
			)
		except ApplicationOutOfScope:
			return ToolResult(ok=False, error=APPLICATION_OUT_OF_SCOPE_ERROR)

		handler = GetApplicationInsightsHandler(SqlAlchemyApplicationInsightsReadRepository(session))
		try:
			insights = await handler.handle(
				GetApplicationInsightsQuery(application=args.application, time_range=args.time_range)
			)
		except UnsupportedInsightsApplication:
			# Not a failure of the caller's: FCI genuinely has no dedicated breakdown, and saying
			# so plainly is more useful than an error the model will read as "try again".
			return ToolResult(
				ok=False,
				error=(
					f"L'application {args.application.value} n'a pas d'analyse détaillée dédiée. "
					"Utilisez les indicateurs et la répartition générale pour cette application."
				),
			)

		payload: dict = {"application": insights.application.value, "time_range": args.time_range.value}
		if insights.coloris_heatmap is not None:
			payload["par_offre_et_version"] = [
				{"offre": cell.offer.value, "version": cell.version.value, "tickets": cell.count}
				for cell in insights.coloris_heatmap
			]
		if insights.aero_top_elements is not None:
			payload["principaux_elements"] = [
				{"element": entry.label.value, "tickets": entry.count} for entry in insights.aero_top_elements
			]
		if insights.vio_app_rows is not None:
			payload["par_application_vio"] = [
				{"vio_app": row.vio_app.value, "ouverts": row.open, "resolus": row.resolved, "total": row.total}
				for row in insights.vio_app_rows
			]
		return ToolResult(ok=True, payload=payload)
	finally:
		await session.close()


GET_APPLICATION_INSIGHTS = ToolSpec(
	name="get_application_insights",
	description=(
		"Retourne l'analyse détaillée propre à une application : répartition par offre et "
		"version pour COLORIS, principaux éléments concernés pour AERO, répartition par "
		"sous-application pour VIO. FCI n'a pas d'analyse dédiée."
	),
	args_model=GetApplicationInsightsArgs,
	required_permission="analytics.read",
	execute=_execute,
)
