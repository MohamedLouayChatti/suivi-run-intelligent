import csv
import io
from datetime import UTC, date, datetime
from typing import Annotated
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
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
from app.modules.ticket_management.application.commands.add_comment_attachment.command import AddCommentAttachmentCommand
from app.modules.ticket_management.application.commands.delete_comment_attachment.command import DeleteCommentAttachmentCommand
from app.modules.ticket_management.application.commands.archive_ticket.command import ArchiveTicketCommand
from app.modules.ticket_management.application.commands.restore_ticket.command import RestoreTicketCommand
from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
from app.modules.ticket_management.application.queries.get_ticket.query import GetTicketQuery
from app.modules.ticket_management.application.queries.download_attachment.query import DownloadAttachmentQuery
from app.modules.ticket_management.application.queries.export_ticket_history.query import ExportTicketHistoryQuery
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.category import Category
from app.modules.ticket_management.domain.enums.status import Status
from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.instance_permissions import require_instance_permission
from app.shared.security.permissions import require_permissions

router = APIRouter(prefix="/tickets", tags=["tickets"])
now = lambda: datetime.now(UTC)

@router.post("", response_model=TicketDetailResponse, status_code=201, dependencies=[Depends(require_permissions("ticket.create"))])
async def create_ticket(payload: Annotated[TicketCreateRequest, Depends(dep.require_ticket_creation_authorized)], current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_create_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(CreateTicketCommand(ticket_id=uuid4(), created_at=now(), assignee_id=current_user.id, actor_id=current_user.id, **payload.model_dump())))

@router.get("", response_model=list[TicketSummaryResponse], dependencies=[Depends(require_permissions("ticket.read"))])
async def list_tickets(handler=Depends(dep.get_list_tickets_handler), allowed_applications: Annotated[frozenset[Application] | None, Depends(dep.require_ticket_read_scope)] = None, page: int = 1, page_size: int = 100):
	query = ListTicketsQuery(limit=page_size, offset=(page-1)*page_size, allowed_applications=allowed_applications)
	return [TicketSummaryResponse.from_dto(x) for x in await handler.handle(query)]

@router.get("/search", response_model=list[TicketSummaryResponse], dependencies=[Depends(require_permissions("ticket.read"))])
async def search_tickets(term: Annotated[str, Query(min_length=1)], handler=Depends(dep.get_search_tickets_handler), allowed_applications: Annotated[frozenset[Application] | None, Depends(dep.require_ticket_read_scope)] = None, page: int = 1, page_size: int = 50):
	query = SearchTicketsQuery(term, limit=page_size, offset=(page-1)*page_size, allowed_applications=allowed_applications)
	return [TicketSummaryResponse.from_dto(x) for x in await handler.handle(query)]

@router.get("/history/export", dependencies=[Depends(require_permissions("ticket.read"))])
async def export_ticket_history(
	handler=Depends(dep.get_export_ticket_history_handler),
	allowed_applications: Annotated[frozenset[Application] | None, Depends(dep.require_ticket_read_scope)] = None,
	application: Application | None = None,
	status_: Annotated[Status | None, Query(alias="status")] = None,
	category: Category | None = None,
	assignee_id: UUID | None = None,
	search: str = "",
	date_from: date | None = None,
	date_to: date | None = None,
):
	query = ExportTicketHistoryQuery(
		application=application, status=status_, category=category, assignee_id=assignee_id,
		search=search, date_from=date_from, date_to=date_to, allowed_applications=allowed_applications,
	)
	tickets = await handler.handle(query)

	buffer = io.StringIO()
	writer = csv.writer(buffer)
	writer.writerow(["ID", "Titre", "Statut", "Assigné à", "Application", "Complété le"])
	for ticket in tickets:
		writer.writerow([
			str(ticket.id), ticket.title, ticket.status.value,
			ticket.assignee.display_name if ticket.assignee else "",
			ticket.application.value, ticket.updated_at.date().isoformat(),
		])
	content = buffer.getvalue().encode("utf-8-sig")
	return Response(
		content=content,
		media_type="text/csv",
		headers={"Content-Disposition": 'attachment; filename="historique_tickets.csv"'},
	)

@router.get("/{ticket_id}", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.read")), Depends(require_instance_permission("ticket", "read", path_param="ticket_id"))])
async def get_ticket(ticket_id: UUID, handler=Depends(dep.get_get_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(GetTicketQuery(ticket_id)))

@router.post("/{ticket_id}/start", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status")), Depends(require_instance_permission("ticket", "start", path_param="ticket_id"))])
async def start_progress(ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_start_progress_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(StartProgressCommand(ticket_id, now(), current_user.id)))

@router.post("/{ticket_id}/resolve", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status")), Depends(require_instance_permission("ticket", "resolve", path_param="ticket_id"))])
async def resolve_ticket(ticket_id: UUID, payload: ResolveRequest, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_resolve_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ResolveTicketCommand(ticket_id, payload.resolution_notes, now(), current_user.id)))

@router.post("/{ticket_id}/close", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status")), Depends(require_instance_permission("ticket", "close", path_param="ticket_id"))])
async def close_ticket(ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_close_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(CloseTicketCommand(ticket_id, now(), current_user.id)))

@router.post("/{ticket_id}/resume", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_status")), Depends(require_instance_permission("ticket", "resume", path_param="ticket_id"))])
async def resume_ticket(ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_resume_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ResumeTicketCommand(ticket_id, now(), current_user.id)))

@router.post("/{ticket_id}/transfer", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.transfer_application")), Depends(require_instance_permission("ticket", "transfer", path_param="ticket_id"))])
async def transfer(ticket_id: UUID, payload: TransferRequest, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_transfer_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(TransferTicketCommand(ticket_id, payload.transferred_to, now(), current_user.id)))

@router.patch("/{ticket_id}/assignee", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.assign")), Depends(require_instance_permission("ticket", "reassign", path_param="ticket_id"))])
async def reassign(ticket_id: UUID, payload: ReassignRequest, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_reassign_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ReassignTicketCommand(ticket_id, payload.assignee_id, now(), current_user.id)))

@router.patch("/{ticket_id}/priority", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.change_priority")), Depends(require_instance_permission("ticket", "change_priority", path_param="ticket_id"))])
async def change_priority(ticket_id: UUID, payload: PriorityUpdateRequest, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_change_priority_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ChangePriorityCommand(ticket_id, payload.priority, now(), current_user.id)))

# Nested resource routers remain public module routes.
comments_router = APIRouter(prefix="/comments", tags=["comments"])
attachments_router = APIRouter(prefix="/attachments", tags=["attachments"])

@router.post("/{ticket_id}/comments", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("comment.create")), Depends(require_instance_permission("comment", "create", path_param="ticket_id"))])
async def add_comment(ticket_id: UUID, payload: CommentCreateRequest, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_add_comment_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(AddCommentCommand(ticket_id=ticket_id, comment_id=uuid4(), created_at=now(), actor_id=current_user.id, **payload.model_dump())))

@router.post("/{ticket_id}/attachments", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("attachment.create")), Depends(require_instance_permission("attachment", "create", path_param="ticket_id"))])
async def add_attachment(ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], file: Annotated[UploadFile, File()], handler=Depends(dep.get_add_ticket_attachment_handler)):
	content = await file.read()
	command = AddTicketAttachmentCommand(
		ticket_id=ticket_id,
		attachment_id=uuid4(),
		filename=file.filename or "unnamed",
		content_type=file.content_type or "application/octet-stream",
		content=content,
		uploaded_by=current_user.id,
		uploaded_at=now(),
	)
	return TicketDetailResponse.from_dto(await handler.handle(command))

@router.post("/{ticket_id}/comments/{comment_id}/attachments", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("attachment.create")), Depends(require_instance_permission("attachment", "create_on_comment", path_param="comment_id"))])
async def add_comment_attachment(ticket_id: UUID, comment_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], file: Annotated[UploadFile, File()], handler=Depends(dep.get_add_comment_attachment_handler)):
	content = await file.read()
	command = AddCommentAttachmentCommand(
		ticket_id=ticket_id,
		comment_id=comment_id,
		attachment_id=uuid4(),
		filename=file.filename or "unnamed",
		content_type=file.content_type or "application/octet-stream",
		content=content,
		uploaded_by=current_user.id,
		uploaded_at=now(),
	)
	return TicketDetailResponse.from_dto(await handler.handle(command))

@comments_router.delete("/{comment_id}/attachments/{attachment_id}", status_code=204, dependencies=[Depends(require_permissions("attachment.delete")), Depends(require_instance_permission("attachment", "delete", path_param="attachment_id"))])
async def delete_comment_attachment(comment_id: UUID, attachment_id: UUID, ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_delete_comment_attachment_handler)):
	await handler.handle(DeleteCommentAttachmentCommand(ticket_id, comment_id, attachment_id, now(), current_user.id))
	return Response(status_code=204)

@router.post("/{ticket_id}/archive", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.archive")), Depends(require_instance_permission("ticket", "archive", path_param="ticket_id"))])
async def archive(ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_archive_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(ArchiveTicketCommand(ticket_id, now(), current_user.id)))

@router.post("/{ticket_id}/restore", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("ticket.restore")), Depends(require_instance_permission("ticket", "restore", path_param="ticket_id"))])
async def restore(ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_restore_ticket_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(RestoreTicketCommand(ticket_id, now(), current_user.id)))

@comments_router.patch("/{comment_id}", response_model=TicketDetailResponse, dependencies=[Depends(require_permissions("comment.update")), Depends(require_instance_permission("comment", "update", path_param="comment_id"))])
async def edit_comment(comment_id: UUID, ticket_id: UUID, payload: CommentUpdateRequest, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_edit_comment_handler)):
	return TicketDetailResponse.from_dto(await handler.handle(EditCommentCommand(ticket_id, comment_id, payload.content, now(), current_user.id)))

@comments_router.delete("/{comment_id}", status_code=204, dependencies=[Depends(require_permissions("comment.delete")), Depends(require_instance_permission("comment", "delete", path_param="comment_id"))])
async def delete_comment(comment_id: UUID, ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_delete_comment_handler)):
	await handler.handle(DeleteCommentCommand(ticket_id, comment_id, now(), current_user.id))
	return Response(status_code=204)

@attachments_router.get("/{attachment_id}", dependencies=[Depends(require_permissions("attachment.read")), Depends(require_instance_permission("attachment", "read", path_param="attachment_id"))])
async def download_attachment(attachment_id: UUID, handler=Depends(dep.get_download_attachment_handler)):
	result = await handler.handle(DownloadAttachmentQuery(attachment_id))
	return Response(
		content=result.content,
		media_type=result.content_type,
		headers={"Content-Disposition": f'attachment; filename="{result.filename}"'},
	)

@attachments_router.delete("/{attachment_id}", status_code=204, dependencies=[Depends(require_permissions("attachment.delete")), Depends(require_instance_permission("attachment", "delete", path_param="attachment_id"))])
async def delete_attachment(attachment_id: UUID, ticket_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler=Depends(dep.get_delete_ticket_attachment_handler)):
	await handler.handle(DeleteTicketAttachmentCommand(ticket_id, attachment_id, now(), current_user.id))
	return Response(status_code=204)
