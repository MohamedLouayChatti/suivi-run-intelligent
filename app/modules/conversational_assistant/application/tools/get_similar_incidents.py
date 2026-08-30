from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.modules.conversational_assistant.application.tools.base import ToolContext, ToolResult, ToolSpec
from app.modules.knowledge_base.application.queries.get_similar_incidents.handler import GetSimilarIncidentsHandler
from app.modules.knowledge_base.application.queries.get_similar_incidents.query import GetSimilarIncidentsQuery
from app.modules.knowledge_base.application.dto.similar_incident_dto import SimilarityAnalysisStatus
from app.modules.knowledge_base.infrastructure.persistence.repositories.sqlalchemy_similarity_read_repository import (
	SqlAlchemySimilarityReadRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store.client import get_qdrant_client
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)


class GetSimilarIncidentsArgs(BaseModel):
	model_config = ConfigDict(extra="forbid")

	ticket_id: UUID


async def _execute(args: GetSimilarIncidentsArgs, ctx: ToolContext) -> ToolResult:
	session = ctx.session_factory()
	try:
		# Gated on read access to the *source* ticket, reusing Ticket Management's own "ticket"
		# policy -- every candidate the handler returns is guaranteed to share the source
		# ticket's application, so nothing further needs checking on the candidates themselves.
		policy = ctx.instance_authorization_registry.resolve("ticket")
		authorization = await policy.authorize(
			current_user=ctx.current_user, resource_id=args.ticket_id, operation="read",
		)
		if not authorization.allowed:
			return ToolResult(ok=False, error="Vous n'êtes pas autorisé à consulter ce ticket.")

		handler = GetSimilarIncidentsHandler(
			SqlAlchemySimilarityReadRepository(session), SqlAlchemyTicketReadRepository(session),
			QdrantKnowledgeItemRepository(get_qdrant_client()),
		)
		result = await handler.handle(GetSimilarIncidentsQuery(ticket_id=args.ticket_id))
		return ToolResult(
			ok=True,
			payload={
				# Carried through rather than collapsed into the empty list, for the reason the
				# field exists at all: a very recently created ticket has not been analysed yet, and
				# a model shown nothing but an empty list would report "aucun incident similaire" --
				# a finding -- when the truthful answer is that the analysis is still running.
				"analysis_status": result.status.value,
				"analysis_pending": result.status is SimilarityAnalysisStatus.PENDING,
				"similar_incidents": [
					{
						"ticket_id": str(incident.ticket_id), "title": incident.title,
						"status": incident.status.value,
						"similarity_score": round(incident.similarity_score, 3),
						"matched_reference": incident.matched_reference,
					}
					for incident in result.incidents
				],
			},
		)
	finally:
		await session.close()


GET_SIMILAR_INCIDENTS = ToolSpec(
	name="get_similar_incidents",
	description=(
		"Retourne les tickets déjà résolus les plus semblables à un ticket donné, avec leur "
		"score de similarité -- utile pour savoir si un incident s'est déjà produit. Si "
		"analysis_pending vaut true, l'analyse du ticket n'est pas encore terminée : la liste est "
		"vide parce qu'il est trop tôt, et non parce qu'aucun incident semblable n'existe."
	),
	args_model=GetSimilarIncidentsArgs,
	required_permission="ticket.read",
	execute=_execute,
	referenced_ticket_ids=lambda payload: [
		incident["ticket_id"] for incident in payload["similar_incidents"]
	],
)
