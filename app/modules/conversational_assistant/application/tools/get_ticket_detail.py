from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.ticket_management.application.exceptions import TicketNotFound
from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
from app.modules.ticket_management.application.queries.get_ticket.query import GetTicketQuery
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)


class GetTicketDetailArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	ticket_id: UUID


async def _execute(args: GetTicketDetailArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		# GetTicketHandler itself performs no instance check -- at the HTTP layer that lives
		# entirely in the route's require_instance_permission("ticket", "read", ...) dependency.
		# This tool bypasses the route, so it reconstructs exactly that check.
		policy = ctx.instance_authorization_registry.resolve("ticket")
		authorization = await policy.authorize(
			current_user=ctx.current_user, resource_id=args.ticket_id, operation="read",
		)
		if not authorization.allowed:
			return ToolResult(ok=False, error="Vous n'êtes pas autorisé à consulter ce ticket.")

		handler = GetTicketHandler(
			SqlAlchemyTicketReadRepository(session), SqlAlchemyUserReadRepository(session),
		)
		try:
			detail = await handler.handle(GetTicketQuery(ticket_id=args.ticket_id))
		except TicketNotFound:
			return ToolResult(ok=False, error="Aucun ticket ne correspond à cet identifiant.")

		return ToolResult(
			ok=True,
			payload={
				"id": str(detail.id),
				"title": detail.title,
				"status": detail.status.value,
				"priority": detail.priority.value,
				"application": detail.application.value,
				"assignee": detail.assignee.display_name if detail.assignee else None,
				"description": detail.description,
				"resolution_notes": detail.resolution_notes,
				"created_at": detail.created_at.isoformat(),
				"comment_count": len(detail.comments),
			},
		)
	finally:
		await session.close()


GET_TICKET_DETAIL = ToolSpec(
	name="get_ticket_detail",
	description=(
		"Récupère les détails complets d'un ticket de support (titre, statut, priorité, "
		"description, notes de résolution) à partir de son identifiant."
	),
	args_model=GetTicketDetailArgs,
	required_permission="ticket.read",
	execute=_execute,
)
