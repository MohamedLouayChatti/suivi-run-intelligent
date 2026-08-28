from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_admin_overview.handler import GetAdminOverviewHandler
from app.modules.analytics.application.queries.get_admin_overview.query import GetAdminOverviewQuery
from app.modules.analytics.application.security.access_scope import (
	READ_ANY_APPLICATION_PERMISSION as ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
)
from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_admin_analytics_read_repository import (
	SqlAlchemyAdminAnalyticsReadRepository,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_health_baseline_repository import (
	SqlAlchemyHealthBaselineRepository,
)
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec

# How many engineers to name per ranking. The underlying read model returns the whole team on five
# separate axes; relaying all of it would be several hundred numbers for a question usually
# answered by "who is carrying the most". Whoever wants one person's full profile has a tool for it.
_TOP_ENGINEERS = 8


class GetAdminOverviewArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	time_range: TimeRange = TimeRange.LAST_3_MONTHS


def _engineers(entries, limit: int = _TOP_ENGINEERS) -> list[dict]:
	ranked = sorted(entries, key=lambda datum: datum.value, reverse=True)[:limit]
	return [
		{
			"engineer": datum.engineer.display_name if datum.engineer else None,
			"engineer_id": str(datum.engineer_id),
			"value": datum.value,
		}
		for datum in ranked
	]


async def _execute(args: GetAdminOverviewArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		handler = GetAdminOverviewHandler(
			SqlAlchemyAdminAnalyticsReadRepository(session),
			SqlAlchemyUserReadRepository(session),
			SqlAlchemyHealthBaselineRepository(session),
		)
		overview = await handler.handle(GetAdminOverviewQuery(time_range=args.time_range))
		return ToolResult(
			ok=True,
			payload={
				"time_range": args.time_range.value,
				"par_application": {
					row.application.value: {
						"ouverts": row.open,
						"en_cours": row.in_progress,
						"resolus": row.resolved,
					}
					for row in overview.workload
				},
				"sante_par_application": {
					entry.application.value: {
						"niveau": entry.health.value,
						"tickets_actifs": entry.active_tickets,
						"tickets_urgents": entry.urgent_tickets,
						"temps_resolution_moyen_h": entry.avg_resolution_hours,
					}
					for entry in overview.health
				},
				"temps_resolution_moyen_h": {
					entry.application.value: entry.avg_resolution_hours for entry in overview.resolution_time
				},
				"dependance_jira": {
					entry.application.value: entry.jira_incidents for entry in overview.jira_dependency
				},
				"taux_transfert_pct": {
					entry.application.value: entry.transfer_rate_pct for entry in overview.transfer_rate
				},
				"tendance_mensuelle": [
					{
						"mois": point.month.isoformat(),
						"par_application": {
							application.value: count for application, count in point.counts.items()
						},
					}
					for point in overview.monthly_trends
				],
				"equipe": {
					"tickets_actifs": _engineers(overview.team.active_tickets),
					"tickets_resolus": _engineers(overview.team.resolved_tickets),
					"temps_resolution_moyen_h": _engineers(overview.team.avg_resolution_hours),
					"repartition_affectations": _engineers(overview.team.assignment_distribution),
					"taux_transfert_pct": _engineers(overview.team.transfer_rate_pct),
				},
			},
		)
	finally:
		await session.close()


GET_ADMIN_OVERVIEW = ToolSpec(
	name="get_admin_overview",
	description=(
		"Retourne la vue transverse de toutes les applications sur une période : charge "
		"(ouverts / en cours / résolus), santé, temps de résolution moyen, dépendance Jira et "
		"taux de transfert par application, tendance mensuelle, plus le classement des "
		"ingénieurs les plus actifs. C'est l'outil à utiliser pour toute question portant sur "
		"« toute l'équipe », « toutes les applications » ou une comparaison entre applications."
	),
	args_model=GetAdminOverviewArgs,
	# The breadth permission itself, not analytics.read: this view is never scoped to a subset of
	# applications, exactly as GET /analytics/admin-overview is never scoped. A caller without it
	# is never offered the tool, so there is no narrower answer to fall back to and nothing to
	# refuse at call time.
	required_permission=ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
	execute=_execute,
)
