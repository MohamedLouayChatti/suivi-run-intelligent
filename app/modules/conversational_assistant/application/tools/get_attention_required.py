from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_attention_required.handler import GetAttentionRequiredHandler
from app.modules.analytics.application.queries.get_attention_required.query import (
	DEFAULT_ATTENTION_THRESHOLD_DAYS, GetAttentionRequiredQuery,
)
from app.modules.analytics.application.security.access_scope import (
	READ_ANY_APPLICATION_PERMISSION as ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_analytics_read_repository import (
	SqlAlchemyAnalyticsReadRepository,
)
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import compute_application_scope
from app.modules.ticket_management.domain.enums.application import Application


class GetAttentionRequiredArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	application: Application | None = None
	threshold_days: int = DEFAULT_ATTENTION_THRESHOLD_DAYS


async def _execute(args: GetAttentionRequiredArgs, ctx: ToolContext) -> ToolResult:
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
		handler = GetAttentionRequiredHandler(
			SqlAlchemyAnalyticsReadRepository(session), SqlAlchemyUserReadRepository(session),
		)
		data = await handler.handle(
			GetAttentionRequiredQuery(
				applications=frozenset(applications) if applications is not None else None,
				threshold_days=args.threshold_days,
			)
		)
		return ToolResult(
			ok=True,
			payload={
				"count": data.count,
				"threshold_days": data.threshold_days,
				# The handler returns only the oldest few in full, which is why `count` can
				# exceed this list -- it is a sample, not the whole set.
				"oldest_incidents": [
					{
						"ticket_id": str(incident.ticket_id), "title": incident.title,
						"age_days": incident.age_days, "priority": incident.priority.value,
						"assignee": incident.assignee.display_name if incident.assignee else None,
					}
					for incident in data.incidents
				],
			},
		)
	finally:
		await session.close()


GET_ATTENTION_REQUIRED = ToolSpec(
	name="get_attention_required",
	description=(
		"Retourne les tickets encore ouverts ou en cours qui traînent depuis plus de "
		f"{DEFAULT_ATTENTION_THRESHOLD_DAYS} jours (seuil ajustable) : leur nombre total et un "
		"échantillon des plus anciens. Photographie instantanée, indépendante de toute période."
	),
	args_model=GetAttentionRequiredArgs,
	required_permission="analytics.read",
	execute=_execute,
	referenced_ticket_ids=lambda payload: [
		incident["ticket_id"] for incident in payload["oldest_incidents"]
	],
)
