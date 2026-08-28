from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.analytics.application.queries.get_resolution_ranking.handler import (
	GetResolutionRankingHandler,
)
from app.modules.analytics.application.queries.get_resolution_ranking.query import (
	MAX_RANKED_TICKETS,
	GetResolutionRankingQuery,
)
from app.modules.analytics.application.security.access_scope import (
	READ_ANY_APPLICATION_PERMISSION as ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
)
from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_read_repository import (
	SqlAlchemyAnalyticsReadRepository,
)
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import (
	APPLICATION_OUT_OF_SCOPE_ERROR,
	ApplicationOutOfScope,
	scoped_applications,
)
from app.modules.ticket_management.domain.enums.application import Application


class GetResolutionRankingArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	application: Application | None = None
	assignee_id: UUID | None = None
	# Optional, and left unset on purpose when the user names no period: "the ticket that took
	# longest" is a question about the whole history, and quietly imposing a window would answer
	# a different one.
	time_range: TimeRange | None = None
	slowest_first: bool = True
	limit: int = Field(default=5, ge=1, le=MAX_RANKED_TICKETS)


async def _execute(args: GetResolutionRankingArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		try:
			applications = scoped_applications(
				ctx.current_user, ANALYTICS_READ_ANY_APPLICATION_PERMISSION, Application, args.application,
			)
		except ApplicationOutOfScope:
			return ToolResult(ok=False, error=APPLICATION_OUT_OF_SCOPE_ERROR)

		handler = GetResolutionRankingHandler(
			SqlAlchemyAnalyticsReadRepository(session), SqlAlchemyUserReadRepository(session),
		)
		ranking = await handler.handle(
			GetResolutionRankingQuery(
				applications=applications, assignee_id=args.assignee_id, time_range=args.time_range,
				slowest_first=args.slowest_first, limit=args.limit,
			)
		)
		return ToolResult(
			ok=True,
			payload={
				"total_resolus": ranking.total_resolved,
				"classement": "du plus long au plus court" if ranking.slowest_first else "du plus court au plus long",
				"periode": "tout l'historique" if args.time_range is None else args.time_range.value,
				"scope": "toutes les applications" if applications is None else sorted(
					application.value for application in applications
				),
				"tickets": [
					{
						"id": str(ticket.ticket_id),
						"title": ticket.title,
						"application": ticket.application.value,
						"priority": ticket.priority.value,
						"assignee": ticket.assignee.display_name if ticket.assignee else None,
						"created_at": ticket.created_at.date().isoformat(),
						"resolved_at": ticket.resolved_at.date().isoformat(),
						"resolution_hours": ticket.resolution_hours,
						"resolution_days": round(ticket.resolution_hours / 24, 1),
					}
					for ticket in ranking.tickets
				],
			},
		)
	finally:
		await session.close()


GET_RESOLUTION_RANKING = ToolSpec(
	name="get_resolution_ranking",
	description=(
		"Classe les tickets résolus par durée de résolution et retourne les plus longs (ou les "
		"plus courts avec slowest_first=false), avec le nombre total de tickets résolus "
		"considérés. Filtrable par application, par ingénieur assigné et par période ; sans "
		"période, le classement porte sur tout l'historique. C'est l'outil à utiliser pour "
		"« quel ticket a pris le plus de temps » ou « les incidents les plus longs »."
	),
	args_model=GetResolutionRankingArgs,
	required_permission="analytics.read",
	execute=_execute,
	referenced_ticket_ids=lambda payload: [ticket["id"] for ticket in payload["tickets"]],
)
