from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.knowledge_base.api import dependencies as dep
from app.modules.knowledge_base.api.schemas.similar_incident import SimilarIncidentResponse
from app.modules.knowledge_base.application.queries.get_similar_incidents.query import GetSimilarIncidentsQuery
from app.shared.security.instance_permissions import require_instance_permission
from app.shared.security.permissions import require_permissions

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])


@router.get(
	"/tickets/{ticket_id}/similar",
	response_model=list[SimilarIncidentResponse],
	dependencies=[
		Depends(require_permissions("ticket.read")),
		Depends(require_instance_permission("ticket", "read", path_param="ticket_id")),
	],
)
async def get_similar_incidents(ticket_id: UUID, handler=Depends(dep.get_get_similar_incidents_handler)):
	incidents = await handler.handle(GetSimilarIncidentsQuery(ticket_id=ticket_id))
	return [SimilarIncidentResponse.from_dto(incident) for incident in incidents]
