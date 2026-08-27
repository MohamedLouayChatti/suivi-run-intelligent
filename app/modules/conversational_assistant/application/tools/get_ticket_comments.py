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

_MAX_COMMENTS = 20


class GetTicketCommentsArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	ticket_id: UUID


async def _execute(args: GetTicketCommentsArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		# Same instance check get_ticket_detail reconstructs, and for the same reason: the
		# comment thread is part of the ticket, so reading it is reading the ticket.
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

		# Soft-deleted comments are withheld: a comment the team removed is not part of the
		# ticket's story any more, and this module has no business resurrecting it into an
		# answer. Oldest first, so the thread reads as the discussion it was.
		comments = [comment for comment in detail.comments if comment.deleted_at is None]
		comments.sort(key=lambda comment: comment.created_at)

		return ToolResult(
			ok=True,
			payload={
				"ticket_id": str(detail.id),
				"title": detail.title,
				"comment_count": len(comments),
				"comments": [
					{
						"author": comment.author.display_name if comment.author else None,
						"created_at": comment.created_at.isoformat(),
						"edited": comment.edited_at is not None,
						"content": comment.content,
					}
					for comment in comments[-_MAX_COMMENTS:]
				],
			},
		)
	finally:
		await session.close()


GET_TICKET_COMMENTS = ToolSpec(
	name="get_ticket_comments",
	description=(
		"Retourne le fil de discussion d'un ticket (auteur, date et contenu de chaque "
		f"commentaire, les {_MAX_COMMENTS} plus récents) -- utile pour comprendre comment un "
		"incident a été diagnostiqué et traité."
	),
	args_model=GetTicketCommentsArgs,
	required_permission="ticket.read",
	execute=_execute,
)
