from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_distributions.handler import GetDistributionsHandler
from app.modules.analytics.application.queries.get_distributions.query import GetDistributionsQuery
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


class GetDistributionsArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	application: Application | None = None
	time_range: TimeRange = TimeRange.LAST_30_DAYS


async def _execute(args: GetDistributionsArgs, ctx: ToolContext) -> ToolResult:
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
		handler = GetDistributionsHandler(SqlAlchemyAnalyticsReadRepository(session))
		distributions = await handler.handle(
			GetDistributionsQuery(
				time_range=args.time_range,
				applications=frozenset(applications) if applications is not None else None,
			)
		)
		return ToolResult(
			ok=True,
			payload={
				"by_status": {key.value: value for key, value in distributions.by_status.items()},
				"by_category": {key.value: value for key, value in distributions.by_category.items()},
				"by_priority": {key.value: value for key, value in distributions.by_priority.items()},
			},
		)
	finally:
		await session.close()


GET_DISTRIBUTIONS = ToolSpec(
	name="get_distributions",
	description=(
		"Retourne la répartition des tickets créés sur une période, par statut, par catégorie "
		"et par priorité, pour une application donnée ou pour les applications de l'utilisateur "
		"-- utile pour savoir sur quels types d'incidents porte l'activité."
	),
	args_model=GetDistributionsArgs,
	required_permission="analytics.read",
	execute=_execute,
)
