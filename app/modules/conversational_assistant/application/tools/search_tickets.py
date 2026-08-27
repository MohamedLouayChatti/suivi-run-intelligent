from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import compute_application_scope
from app.modules.ticket_management.application.queries.list_tickets.handler import ListTicketsHandler
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.application.security.support import READ_ANY_APPLICATION_PERMISSION
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)

_MAX_RESULTS = 15


class SearchTicketsArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	# Optional, not required: the filters below are a complete question on their own ("les
	# tickets critiques de tel ingénieur"), and a required keyword forced the model to invent
	# one -- typically a person's name, which the keyword search cannot match at all, since it
	# reads title and description and an assignee is a foreign key.
	term: str | None = None
	application: Application | None = None
	status: Status | None = None
	priority: Priority | None = None
	category: Category | None = None
	# Resolve a person to their id with lookup_engineer first; this tool never takes a name.
	assignee_id: UUID | None = None
	operational_highlight: bool | None = None


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

		read_repository = SqlAlchemyTicketReadRepository(session)
		user_repository = SqlAlchemyUserReadRepository(session)
		term = (args.term or "").strip()

		# Two handlers, one tool: with a keyword this is Ticket Management's own search (title
		# and description), without one it is its list query, which also reports how many
		# tickets matched beyond the page -- the number the model needs to answer "combien".
		if term:
			results = await SearchTicketsHandler(read_repository, user_repository).handle(
				SearchTicketsQuery(
					term=term, application=args.application, status=args.status,
					priority=args.priority, category=args.category, assignee_id=args.assignee_id,
					operational_highlight=args.operational_highlight,
					limit=_MAX_RESULTS, allowed_applications=allowed_applications,
				)
			)
			total = len(results)
		else:
			page = await ListTicketsHandler(read_repository, user_repository).handle(
				ListTicketsQuery(
					application=args.application, status=args.status, priority=args.priority,
					category=args.category, assignee_id=args.assignee_id,
					operational_highlight=args.operational_highlight,
					limit=_MAX_RESULTS, allowed_applications=allowed_applications,
				)
			)
			results, total = page.items, page.total

		return ToolResult(
			ok=True,
			payload={
				"total_matching": total,
				"returned": len(results),
				"tickets": [
					{
						"id": str(ticket.id), "title": ticket.title, "status": ticket.status.value,
						"priority": ticket.priority.value, "application": ticket.application.value,
						"category": ticket.category.value,
						"assignee": ticket.assignee.display_name if ticket.assignee else None,
						"created_at": ticket.created_at.date().isoformat(),
					}
					for ticket in results
				],
			},
		)
	finally:
		await session.close()


SEARCH_TICKETS = ToolSpec(
	name="search_tickets",
	description=(
		"Recherche des tickets. Le mot-clé est optionnel et porte sur le titre et la "
		"description : omettez-le pour lister les tickets correspondant uniquement aux filtres "
		"(application, statut, priorité, catégorie, ingénieur assigné, fait marquant). "
		"Pour les tickets d'une personne, résolvez d'abord son identifiant avec lookup_engineer "
		"puis passez-le dans assignee_id -- son nom n'apparaît pas dans le texte des tickets. "
		f"Retourne au plus {_MAX_RESULTS} tickets, avec le nombre total de correspondances."
	),
	args_model=SearchTicketsArgs,
	required_permission="ticket.read",
	execute=_execute,
)
