from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import compute_application_scope
from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.application.security.support import READ_ANY_APPLICATION_PERMISSION
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)

_MAX_RESULTS = 15


class SearchTicketsArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	term: str
	application: Application | None = None
	status: Status | None = None


async def _execute(args: SearchTicketsArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		allowed_applications = compute_application_scope(
			ctx.current_user, READ_ANY_APPLICATION_PERMISSION, Application,
		)
		if (
			allowed_applications is not None
			and args.application is not None
			and args.application not in allowed_applications
		):
			return ToolResult(
				ok=False,
				error="Vous n'avez pas accès aux tickets de cette application.",
			)

		handler = SearchTicketsHandler(
			SqlAlchemyTicketReadRepository(session), SqlAlchemyUserReadRepository(session),
		)
		results = await handler.handle(
			SearchTicketsQuery(
				term=args.term, application=args.application, status=args.status,
				limit=_MAX_RESULTS, allowed_applications=allowed_applications,
			)
		)
		return ToolResult(
			ok=True,
			payload={
				"tickets": [
					{
						"id": str(ticket.id), "title": ticket.title, "status": ticket.status.value,
						"priority": ticket.priority.value, "application": ticket.application.value,
					}
					for ticket in results
				]
			},
		)
	finally:
		await session.close()


SEARCH_TICKETS = ToolSpec(
	name="search_tickets",
	description=(
		"Recherche des tickets par mot-clé, avec filtres optionnels d'application et de statut. "
		f"Retourne au plus {_MAX_RESULTS} résultats."
	),
	args_model=SearchTicketsArgs,
	required_permission="ticket.read",
	execute=_execute,
)
