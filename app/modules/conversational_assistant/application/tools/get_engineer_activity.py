from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.analytics.application.queries.get_engineer_activity.handler import GetEngineerActivityHandler
from app.modules.analytics.application.queries.get_engineer_activity.query import GetEngineerActivityQuery
from app.modules.analytics.application.security.access_scope import (
	READ_ANY_APPLICATION_PERMISSION as ANALYTICS_READ_ANY_APPLICATION_PERMISSION,
)
from app.modules.analytics.application.support.time_range import TimeRange
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_engineer_activity_read_repository import (
	SqlAlchemyEngineerActivityReadRepository,
)
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import compute_application_scope
from app.modules.ticket_management.domain.enums.application import Application


class GetEngineerActivityArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	engineer_id: UUID
	time_range: TimeRange = TimeRange.LAST_6_MONTHS


def _non_zero(counts: dict) -> dict[str, int]:
	"""Only the buckets an engineer actually worked in. The repository returns every enum
	member, zeros included, because that is what a chart needs; a sentence about somebody's
	work does not, and the empty ones are noise the model would have to filter itself."""
	return {key.value: value for key, value in counts.items() if value}


async def _execute(args: GetEngineerActivityArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		# Application-scoped, not breadth-gated: an engineer may ask about a colleague, but only
		# over the applications they can already report on. Holding
		# analytics.read_any_application lifts the narrowing entirely, exactly as it does on
		# every other analytics read.
		allowed_applications = compute_application_scope(
			ctx.current_user, ANALYTICS_READ_ANY_APPLICATION_PERMISSION, Application,
		)
		handler = GetEngineerActivityHandler(
			SqlAlchemyEngineerActivityReadRepository(session), SqlAlchemyUserReadRepository(session),
		)
		activity = await handler.handle(
			GetEngineerActivityQuery(
				engineer_id=args.engineer_id, time_range=args.time_range,
				applications=allowed_applications,
			)
		)
		return ToolResult(
			ok=True,
			payload={
				"engineer": activity.engineer.display_name if activity.engineer else None,
				"time_range": args.time_range.value,
				"scope": (
					"toutes les applications" if allowed_applications is None
					else sorted(application.value for application in allowed_applications)
				),
				"active_tickets": activity.active_tickets,
				"created_tickets": activity.created_tickets,
				"resolved_tickets": activity.resolved_tickets,
				"avg_resolution_hours": activity.avg_resolution_hours,
				"transfer_rate_pct": activity.transfer_rate_pct,
				"tickets_by_application": _non_zero(activity.by_application),
				"tickets_by_category": _non_zero(activity.by_category),
				"tickets_by_status": _non_zero(activity.by_status),
			},
		)
	finally:
		await session.close()


GET_ENGINEER_ACTIVITY = ToolSpec(
	name="get_engineer_activity",
	description=(
		"Retourne le profil d'activité d'un ingénieur : tickets actifs, créés et résolus, temps "
		"de résolution moyen, taux de transfert, et répartition de ses tickets par application, "
		"catégorie et statut. Prend un identifiant d'ingénieur, à résoudre au préalable avec "
		"lookup_engineer. Les chiffres sont limités aux applications que l'utilisateur peut "
		"consulter."
	),
	args_model=GetEngineerActivityArgs,
	required_permission="analytics.read",
	execute=_execute,
)
