from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.ticket_management.api.dependencies import (
	get_add_comment_handler, get_add_ticket_attachment_handler, get_archive_ticket_handler,
	get_assign_ticket_handler, get_change_priority_handler, get_change_status_handler,
	get_create_ticket_handler, get_delete_comment_handler, get_delete_ticket_attachment_handler,
	get_edit_comment_handler, get_get_ticket_handler, get_list_tickets_handler,
	get_restore_ticket_handler, get_search_tickets_handler, get_transfer_application_handler,
)
from app.modules.ticket_management.api.schemas import (
	ApplicationUpdateRequest, AssignmentUpdateRequest, AttachmentCreateRequest,
	CommentCreateRequest, CommentUpdateRequest, PriorityUpdateRequest, StatusUpdateRequest,
	TicketCreateRequest, TicketDetailResponse, TicketSummaryResponse,
)
from app.modules.ticket_management.application.commands.add_comment.command import AddCommentCommand
from app.modules.ticket_management.application.commands.add_comment.handler import AddCommentHandler
from app.modules.ticket_management.application.commands.add_ticket_attachment.command import AddTicketAttachmentCommand
from app.modules.ticket_management.application.commands.add_ticket_attachment.handler import AddTicketAttachmentHandler
from app.modules.ticket_management.application.commands.archive_ticket.command import ArchiveTicketCommand
from app.modules.ticket_management.application.commands.archive_ticket.handler import ArchiveTicketHandler
from app.modules.ticket_management.application.commands.assign_ticket.command import AssignTicketCommand
from app.modules.ticket_management.application.commands.assign_ticket.handler import AssignTicketHandler
from app.modules.ticket_management.application.commands.change_priority.command import ChangePriorityCommand
from app.modules.ticket_management.application.commands.change_priority.handler import ChangePriorityHandler
from app.modules.ticket_management.application.commands.change_status.command import ChangeStatusCommand
from app.modules.ticket_management.application.commands.change_status.handler import ChangeStatusHandler
from app.modules.ticket_management.application.commands.create_ticket.command import CreateTicketCommand
from app.modules.ticket_management.application.commands.create_ticket.handler import CreateTicketHandler
from app.modules.ticket_management.application.commands.delete_comment.command import DeleteCommentCommand
from app.modules.ticket_management.application.commands.delete_comment.handler import DeleteCommentHandler
from app.modules.ticket_management.application.commands.delete_ticket_attachment.command import DeleteTicketAttachmentCommand
from app.modules.ticket_management.application.commands.delete_ticket_attachment.handler import DeleteTicketAttachmentHandler
from app.modules.ticket_management.application.commands.edit_comment.command import EditCommentCommand
from app.modules.ticket_management.application.commands.edit_comment.handler import EditCommentHandler
from app.modules.ticket_management.application.commands.restore_ticket.command import RestoreTicketCommand
from app.modules.ticket_management.application.commands.restore_ticket.handler import RestoreTicketHandler
from app.modules.ticket_management.application.commands.transfer_application.command import TransferApplicationCommand
from app.modules.ticket_management.application.commands.transfer_application.handler import TransferApplicationHandler
from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
from app.modules.ticket_management.application.queries.get_ticket.query import GetTicketQuery
from app.modules.ticket_management.application.queries.list_tickets.handler import ListTicketsHandler
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(payload: TicketCreateRequest, handler: Annotated[CreateTicketHandler, Depends(get_create_ticket_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(CreateTicketCommand(ticket_id=uuid4(), created_at=datetime.now(UTC), **payload.model_dump()))
	return TicketDetailResponse.from_dto(ticket)


@router.get("/search", response_model=list[TicketSummaryResponse])
async def search_tickets(term: Annotated[str, Query(min_length=1)], page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 50, handler: Annotated[SearchTicketsHandler, Depends(get_search_tickets_handler)] = None) -> list[TicketSummaryResponse]:
	tickets = await handler.handle(SearchTicketsQuery(term=term, limit=page_size, offset=(page - 1) * page_size))
	return [TicketSummaryResponse.from_dto(ticket) for ticket in tickets]


@router.get("", response_model=list[TicketSummaryResponse])
async def list_tickets(page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 100, handler: Annotated[ListTicketsHandler, Depends(get_list_tickets_handler)] = None) -> list[TicketSummaryResponse]:
	tickets = await handler.handle(ListTicketsQuery(limit=page_size, offset=(page - 1) * page_size))
	return [TicketSummaryResponse.from_dto(ticket) for ticket in tickets]


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
async def get_ticket(ticket_id: UUID, handler: Annotated[GetTicketHandler, Depends(get_get_ticket_handler)]) -> TicketDetailResponse:
	return TicketDetailResponse.from_dto(await handler.handle(GetTicketQuery(ticket_id=ticket_id)))


@router.patch("/{ticket_id}/assignment", response_model=TicketDetailResponse)
async def assign_ticket(ticket_id: UUID, payload: AssignmentUpdateRequest, handler: Annotated[AssignTicketHandler, Depends(get_assign_ticket_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(AssignTicketCommand(ticket_id=ticket_id, assignee_id=payload.assignee_id, assigned_at=datetime.now(UTC)))
	return TicketDetailResponse.from_dto(ticket)


@router.patch("/{ticket_id}/priority", response_model=TicketDetailResponse)
async def change_priority(ticket_id: UUID, payload: PriorityUpdateRequest, handler: Annotated[ChangePriorityHandler, Depends(get_change_priority_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(ChangePriorityCommand(ticket_id=ticket_id, priority=payload.priority, changed_at=datetime.now(UTC)))
	return TicketDetailResponse.from_dto(ticket)


@router.patch("/{ticket_id}/status", response_model=TicketDetailResponse)
async def change_status(ticket_id: UUID, payload: StatusUpdateRequest, handler: Annotated[ChangeStatusHandler, Depends(get_change_status_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(ChangeStatusCommand(ticket_id=ticket_id, changed_at=datetime.now(UTC), **payload.model_dump()))
	return TicketDetailResponse.from_dto(ticket)


@router.patch("/{ticket_id}/application", response_model=TicketDetailResponse)
async def transfer_application(ticket_id: UUID, payload: ApplicationUpdateRequest, handler: Annotated[TransferApplicationHandler, Depends(get_transfer_application_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(TransferApplicationCommand(ticket_id=ticket_id, new_application=payload.application, new_assignee=payload.assignee_id, transferred_at=datetime.now(UTC)))
	return TicketDetailResponse.from_dto(ticket)


@router.post("/{ticket_id}/comments", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(ticket_id: UUID, payload: CommentCreateRequest, handler: Annotated[AddCommentHandler, Depends(get_add_comment_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(AddCommentCommand(ticket_id=ticket_id, comment_id=uuid4(), created_at=datetime.now(UTC), **payload.model_dump()))
	return TicketDetailResponse.from_dto(ticket)


@router.post("/{ticket_id}/attachments", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
async def add_ticket_attachment(ticket_id: UUID, payload: AttachmentCreateRequest, handler: Annotated[AddTicketAttachmentHandler, Depends(get_add_ticket_attachment_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(AddTicketAttachmentCommand(ticket_id=ticket_id, attachment_id=uuid4(), uploaded_at=datetime.now(UTC), **payload.model_dump()))
	return TicketDetailResponse.from_dto(ticket)


@router.post("/{ticket_id}/archive", response_model=TicketDetailResponse)
async def archive_ticket(ticket_id: UUID, handler: Annotated[ArchiveTicketHandler, Depends(get_archive_ticket_handler)]) -> TicketDetailResponse:
	return TicketDetailResponse.from_dto(await handler.handle(ArchiveTicketCommand(ticket_id=ticket_id, archived_at=datetime.now(UTC))))


@router.post("/{ticket_id}/restore", response_model=TicketDetailResponse)
async def restore_ticket(ticket_id: UUID, handler: Annotated[RestoreTicketHandler, Depends(get_restore_ticket_handler)]) -> TicketDetailResponse:
	return TicketDetailResponse.from_dto(await handler.handle(RestoreTicketCommand(ticket_id=ticket_id, restored_at=datetime.now(UTC))))


comments_router = APIRouter(prefix="/comments", tags=["comments"])


@comments_router.patch("/{comment_id}", response_model=TicketDetailResponse)
async def edit_comment(comment_id: UUID, ticket_id: UUID, payload: CommentUpdateRequest, handler: Annotated[EditCommentHandler, Depends(get_edit_comment_handler)]) -> TicketDetailResponse:
	ticket = await handler.handle(EditCommentCommand(ticket_id=ticket_id, comment_id=comment_id, content=payload.content, edited_at=datetime.now(UTC)))
	return TicketDetailResponse.from_dto(ticket)


@comments_router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: UUID, ticket_id: UUID, handler: Annotated[DeleteCommentHandler, Depends(get_delete_comment_handler)]) -> Response:
	await handler.handle(DeleteCommentCommand(ticket_id=ticket_id, comment_id=comment_id, deleted_at=datetime.now(UTC)))
	return Response(status_code=status.HTTP_204_NO_CONTENT)


attachments_router = APIRouter(prefix="/attachments", tags=["attachments"])


@attachments_router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_attachment(attachment_id: UUID, ticket_id: UUID, handler: Annotated[DeleteTicketAttachmentHandler, Depends(get_delete_ticket_attachment_handler)]) -> Response:
	await handler.handle(DeleteTicketAttachmentCommand(ticket_id=ticket_id, attachment_id=attachment_id, deleted_at=datetime.now(UTC)))
	return Response(status_code=status.HTTP_204_NO_CONTENT)
