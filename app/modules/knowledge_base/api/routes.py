from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.modules.knowledge_base.api import dependencies as dep
from app.modules.knowledge_base.api.schemas.recalculation_schedule import (
	RecalculationScheduleResponse,
	UpdateRecalculationScheduleRequest,
)
from app.modules.knowledge_base.api.schemas.similar_incident import SimilarIncidentResponse
from app.modules.knowledge_base.application.commands.trigger_similarity_recalculation.command import (
	TriggerSimilarityRecalculationCommand,
)
from app.modules.knowledge_base.application.commands.update_recalculation_schedule.command import (
	UpdateRecalculationScheduleCommand,
)
from app.modules.knowledge_base.application.queries.get_recalculation_schedule.query import (
	GetRecalculationScheduleQuery,
)
from app.modules.knowledge_base.application.queries.get_similar_incidents.query import GetSimilarIncidentsQuery
from app.shared.security.current_user import CurrentUser, get_current_user
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


# The three routes below are maintenance rather than retrieval, and are gated by permissions of
# their own rather than by any of the ticket ones above: they configure and start a pass over the
# entire corpus, which is not an operation on a resource anybody owns. Both are seeded onto Admin
# alone -- as ever, that is where they happen to be granted, not a role check.


@router.get(
	"/recalculation-schedule",
	response_model=RecalculationScheduleResponse,
	dependencies=[Depends(require_permissions("knowledge_base.read_recalculation"))],
)
async def get_recalculation_schedule(handler=Depends(dep.get_get_recalculation_schedule_handler)):
	return RecalculationScheduleResponse.from_dto(await handler.handle(GetRecalculationScheduleQuery()))


@router.put(
	"/recalculation-schedule",
	response_model=RecalculationScheduleResponse,
	dependencies=[Depends(require_permissions("knowledge_base.manage_recalculation"))],
)
async def update_recalculation_schedule(
	payload: UpdateRecalculationScheduleRequest,
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_update_recalculation_schedule_handler),
):
	command = UpdateRecalculationScheduleCommand(
		enabled=payload.enabled,
		days_of_week=frozenset(payload.days_of_week),
		hour=payload.hour,
		minute=payload.minute,
		timezone=payload.timezone,
		updated_at=datetime.now(UTC),
		actor_id=current_user.id,
	)
	return RecalculationScheduleResponse.from_dto(await handler.handle(command))


@router.post(
	"/recalculation/run",
	status_code=status.HTTP_202_ACCEPTED,
	dependencies=[Depends(require_permissions("knowledge_base.manage_recalculation"))],
)
async def run_recalculation_now(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_trigger_similarity_recalculation_handler),
):
	"""Start a full recalculation now, outside the schedule.

	202 with no body, because that is what actually happened: the pass was accepted and will run
	in the background, long after this response. Its progress and outcome are in the log, and
	whether one is running is on the schedule endpoint above. A run requested while another is
	already in flight is refused with 409 rather than queued.
	"""
	await handler.handle(TriggerSimilarityRecalculationCommand(actor_id=current_user.id))
	return Response(status_code=status.HTTP_202_ACCEPTED)
