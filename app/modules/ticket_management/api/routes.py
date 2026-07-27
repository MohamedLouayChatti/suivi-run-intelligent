from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query, Response, status
from app.modules.ticket_management.api import dependencies as dep
from app.modules.ticket_management.api.schemas import *
from app.modules.ticket_management.application.commands.create_ticket.command import CreateTicketCommand
from app.modules.ticket_management.application.commands.start_progress.command import StartProgressCommand
from app.modules.ticket_management.application.commands.resolve_ticket.command import ResolveTicketCommand
from app.modules.ticket_management.application.commands.close_ticket.command import CloseTicketCommand
from app.modules.ticket_management.application.commands.resume_ticket.command import ResumeTicketCommand
from app.modules.ticket_management.application.commands.transfer_ticket.command import TransferTicketCommand
from app.modules.ticket_management.application.commands.reassign_ticket.command import ReassignTicketCommand
from app.modules.ticket_management.application.commands.change_priority.command import ChangePriorityCommand
from app.modules.ticket_management.application.commands.add_comment.command import AddCommentCommand
from app.modules.ticket_management.application.commands.edit_comment.command import EditCommentCommand
from app.modules.ticket_management.application.commands.delete_comment.command import DeleteCommentCommand
from app.modules.ticket_management.application.commands.add_ticket_attachment.command import AddTicketAttachmentCommand
from app.modules.ticket_management.application.commands.delete_ticket_attachment.command import DeleteTicketAttachmentCommand
from app.modules.ticket_management.application.commands.archive_ticket.command import ArchiveTicketCommand
from app.modules.ticket_management.application.commands.restore_ticket.command import RestoreTicketCommand
from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
from app.modules.ticket_management.application.queries.get_ticket.query import GetTicketQuery
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.shared.security.permissions import require_permissions

router = APIRouter(prefix="/tickets", tags=["tickets"])
now = lambda: datetime.now(UTC)

@router.post("", response_model=TicketDetailResponse, status_code=201, dependencies=[Depends(require_permissions("ticket.create"))])
async def create_ticket(payload: TicketCreateRequest, handler=Depends(dep.get_create_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(CreateTicketCommand(ticket_id=uuid4(), created_at=now(), **payload.model_dump())))

@router.get("", response_model=list[TicketSummaryResponse], dependencies=[Depends(require_permissions("ticket.read"))])
async def list_tickets(handler=Depends(dep.get_list_tickets_handler), page: int = 1, page_size: int = 100):
	return [TicketSummaryResponse.from_dto(x) for x in await handler.handle(ListTicketsQuery(limit=page_size, offset=(page-1)*page_size))]

@router.get("/search", response_model=list[TicketSummaryResponse], dependencies=[Depends(require_permissions("ticket.read"))])
async def search_tickets(term: Annotated[str, Query(min_length=1)], handler=Depends(dep.get_search_tickets_handler), page: int = 1, page_size: int = 50):
	return [TicketSummaryResponse.from_dto(x) for x in await handler.handle(SearchTicketsQuery(term, limit=page_size, offset=(page-1)*page_size))]

@router.get("/{ticket_id}", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.read"))])
async def get_ticket(ticket_id: UUID, handler=Depends(dep.get_get_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(GetTicketQuery(ticket_id)))

@router.post("/{ticket_id}/start", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status"))])
async def start_progress(ticket_id: UUID, handler=Depends(dep.get_start_progress_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(StartProgressCommand(ticket_id, now())))

@router.post("/{ticket_id}/resolve", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status"))])
async def resolve_ticket(ticket_id: UUID, payload: ResolveRequest, handler=Depends(dep.get_resolve_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ResolveTicketCommand(ticket_id, payload.resolution_notes, now())))

@router.post("/{ticket_id}/close", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status"))])
async def close_ticket(ticket_id: UUID, handler=Depends(dep.get_close_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(CloseTicketCommand(ticket_id, now())))

@router.post("/{ticket_id}/resume", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status"))])
async def resume_ticket(ticket_id: UUID, handler=Depends(dep.get_resume_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ResumeTicketCommand(ticket_id, now())))

@router.post("/{ticket_id}/transfer", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.transfer_application"))])
async def transfer(ticket_id: UUID, payload: TransferRequest, handler=Depends(dep.get_transfer_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(TransferTicketCommand(ticket_id, payload.transferred_to, now())))

@router.patch("/{ticket_id}/assignee", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.assign"))])
async def reassign(ticket_id: UUID, payload: ReassignRequest, handler=Depends(dep.get_reassign_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ReassignTicketCommand(ticket_id, payload.assignee_id, now())))

@router.patch("/{ticket_id}/priority", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_priority"))])
async def change_priority(ticket_id: UUID, payload: PriorityUpdateRequest, handler=Depends(dep.get_change_priority_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ChangePriorityCommand(ticket_id, payload.priority, now())))

# Nested resource routers remain public module routes.
comments_router = APIRouter(prefix="/comments", tags=["comments"])
attachments_router = APIRouter(prefix="/attachments", tags=["attachments"])

@router.post("/{ticket_id}/comments", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("comment.create"))])
async def add_comment(ticket_id: UUID, payload: CommentCreateRequest, handler=Depends(dep.get_add_comment_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(AddCommentCommand(ticket_id=ticket_id, comment_id=uuid4(), created_at=now(), **payload.model_dump())))

@router.post("/{ticket_id}/attachments", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("attachment.create"))])
async def add_attachment(ticket_id: UUID, payload: AttachmentCreateRequest, handler=Depends(dep.get_add_ticket_attachment_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(AddTicketAttachmentCommand(ticket_id=ticket_id, attachment_id=uuid4(), uploaded_at=now(), **payload.model_dump())))

@router.post("/{ticket_id}/archive", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.archive"))])
async def archive(ticket_id: UUID, handler=Depends(dep.get_archive_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ArchiveTicketCommand(ticket_id, now())))

@router.post("/{ticket_id}/restore", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.restore"))])
async def restore(ticket_id: UUID, handler=Depends(dep.get_restore_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(RestoreTicketCommand(ticket_id, now())))

@comments_router.patch("/{comment_id}", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("comment.update"))])
async def edit_comment(comment_id: UUID, ticket_id: UUID, payload: CommentUpdateRequest, handler=Depends(dep.get_edit_comment_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(EditCommentCommand(ticket_id, comment_id, payload.content, now())))

@comments_router.delete("/{comment_id}", status_code=204, dependencies=[Depends(require_permissions("comment.delete"))])
async def delete_comment(comment_id: UUID, ticket_id: UUID, handler=Depends(dep.get_delete_comment_handler)):
	await handler.handle(DeleteCommentCommand(ticket_id, comment_id, now()))
	return Response(status_code=204)

@attachments_router.delete("/{attachment_id}", status_code=204, dependencies=[Depends(require_permissions("attachment.delete"))])
async def delete_attachment(attachment_id: UUID, ticket_id: UUID, handler=Depends(dep.get_delete_ticket_attachment_handler)):
	await handler.handle(DeleteTicketAttachmentCommand(ticket_id, attachment_id, now()))
	return Response(status_code=204)
