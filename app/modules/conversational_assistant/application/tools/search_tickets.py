from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import (
	SqlAlchemyUserReadRepository,
)
from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.conversational_assistant.application.tools.support import (
	APPLICATION_OUT_OF_SCOPE_ERROR,
	ApplicationOutOfScope,
	compute_application_scope,
	scoped_applications,
)
from app.modules.ticket_management.application.queries.list_tickets.handler import ListTicketsHandler
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.application.security.support import READ_ANY_APPLICATION_PERMISSION
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)

_DEFAULT_RESULTS = 15
_MAX_RESULTS = 40


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
	functional_team: FunctionalTeam | None = None
	# Resolve a person to their id with lookup_engineer first; this tool never takes a name.
	assignee_id: UUID | None = None
	operational_highlight: bool | None = None
	# Creation-date window. A question is very often bounded by one ("les tickets de juin", "ce
	# trimestre"), and without these the only way to honour it was to page through everything and
	# filter by eye -- which the result cap made unreliable and the iteration budget made costly.
	created_from: date | None = None
	created_to: date | None = None
	include_archived: bool = False
	limit: int = Field(default=_DEFAULT_RESULTS, ge=1, le=_MAX_RESULTS)


async def _execute(args: SearchTicketsArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		try:
			applications = scoped_applications(
				ctx.current_user, READ_ANY_APPLICATION_PERMISSION, Application, args.application,
			)
		except ApplicationOutOfScope:
			return ToolResult(ok=False, error=APPLICATION_OUT_OF_SCOPE_ERROR)

		# The query layer takes the caller's whole permitted set and intersects any explicit
		# application filter itself, so an application named here is passed as a filter rather
		# than folded into the scope -- keeping "may not look there" and "chose to look here"
		# distinguishable in the query, exactly as the HTTP routes keep them.
		allowed_applications = compute_application_scope(
			ctx.current_user, READ_ANY_APPLICATION_PERMISSION, Application,
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
					functional_team=args.functional_team,
					operational_highlight=args.operational_highlight,
					created_from=args.created_from, created_to=args.created_to,
					include_archived=args.include_archived,
					limit=args.limit, allowed_applications=allowed_applications,
				)
			)
			total = len(results)
		else:
			page = await ListTicketsHandler(read_repository, user_repository).handle(
				ListTicketsQuery(
					application=args.application, status=args.status, priority=args.priority,
					category=args.category, assignee_id=args.assignee_id,
					functional_team=args.functional_team,
					operational_highlight=args.operational_highlight,
					created_from=args.created_from, created_to=args.created_to,
					include_archived=args.include_archived,
					limit=args.limit, allowed_applications=allowed_applications,
				)
			)
			results, total = page.items, page.total

		return ToolResult(
			ok=True,
			payload={
				"total_matching": total,
				"returned": len(results),
				# Said plainly rather than left to be inferred from the two numbers above: a model
				# that reads 15 of 280 rows as "the whole set" answers "which is the oldest" with
				# whatever happens to be on the page, which is how a sample became an assertion.
				"is_sample": total > len(results),
				"scope": "toutes les applications" if applications is None else sorted(
					application.value for application in applications
				),
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
		"(application, statut, priorité, catégorie, équipe fonctionnelle, ingénieur assigné, "
		"fait marquant, date de création). "
		"Pour les tickets d'une personne, résolvez d'abord son identifiant avec lookup_engineer "
		"puis passez-le dans assignee_id -- son nom n'apparaît pas dans le texte des tickets. "
		f"Retourne au plus {_MAX_RESULTS} tickets, avec le nombre total de correspondances : "
		"quand ce total dépasse le nombre retourné, la liste est un échantillon et ne permet pas "
		"de conclure sur l'ensemble."
	),
	args_model=SearchTicketsArgs,
	required_permission="ticket.read",
	execute=_execute,
	referenced_ticket_ids=lambda payload: [ticket["id"] for ticket in payload["tickets"]],
)
