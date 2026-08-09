from collections.abc import AsyncIterator
from typing import Annotated, cast
from fastapi import Depends, HTTPException, Request, status
from app.modules.ticket_management.api.schemas.ticket import TicketCreateRequest
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.application.security.ticket_access_policy import TicketAccessPolicy
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import SqlAlchemyTicketReadRepository
from app.modules.ticket_management.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.database.session import create_session
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry
from app.modules.auth.api.dependencies import get_user_read_repository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import SqlAlchemyUserReadRepository
from app.shared.storage.local_storage_service import storage_service as _storage_service
from app.shared.storage.service import StorageService


async def require_ticket_creation_authorized(
	request: Request,
	payload: TicketCreateRequest,
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> TicketCreateRequest:
	registry: InstanceAuthorizationRegistry = request.app.state.instance_authorization_registry
	policy = cast(TicketAccessPolicy, registry.resolve("ticket"))
	result = await policy.authorize_creation(current_user=current_user, application=payload.application, functional_team=payload.functional_team)
	if not result.allowed:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result.reason)
	return payload


async def require_ticket_read_scope(
	request: Request,
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> frozenset[Application] | None:
	registry: InstanceAuthorizationRegistry = request.app.state.instance_authorization_registry
	policy = cast(TicketAccessPolicy, registry.resolve("ticket"))
	return await policy.allowed_applications_filter(current_user=current_user)

async def get_unit_of_work() -> AsyncIterator[SqlAlchemyUnitOfWork]:
	uow = SqlAlchemyUnitOfWork()
	try: yield uow
	finally: await uow.close()

async def get_read_repository() -> AsyncIterator[SqlAlchemyTicketReadRepository]:
	session = create_session()
	try: yield SqlAlchemyTicketReadRepository(session)
	finally: await session.close()

def get_event_publisher(request: Request) -> InMemoryEventPublisher:
	return InMemoryEventPublisher(request.app.state.event_bus)

def get_storage_service() -> StorageService:
	return _storage_service

def _command_handler(handler_type, uow, publisher): return handler_type(uow, publisher)

def get_create_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
	from app.modules.ticket_management.application.commands.create_ticket.handler import CreateTicketHandler
	return _command_handler(CreateTicketHandler, uow, publisher)

def get_reassign_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)], users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]):
	from app.modules.ticket_management.application.commands.reassign_ticket.handler import ReassignTicketHandler
	return ReassignTicketHandler(uow, publisher, users)

def _provider(name):
	def provider(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
		module, cls = name.rsplit(".", 1)
		obj = __import__(module, fromlist=[cls]).__dict__[cls]
		return obj(uow, publisher)
	return provider

get_start_progress_handler = _provider("app.modules.ticket_management.application.commands.start_progress.handler.StartProgressHandler")
get_resolve_ticket_handler = _provider("app.modules.ticket_management.application.commands.resolve_ticket.handler.ResolveTicketHandler")
get_close_ticket_handler = _provider("app.modules.ticket_management.application.commands.close_ticket.handler.CloseTicketHandler")
get_resume_ticket_handler = _provider("app.modules.ticket_management.application.commands.resume_ticket.handler.ResumeTicketHandler")
get_transfer_ticket_handler = _provider("app.modules.ticket_management.application.commands.transfer_ticket.handler.TransferTicketHandler")
get_update_jira_details_handler = _provider("app.modules.ticket_management.application.commands.update_jira_details.handler.UpdateJiraDetailsHandler")
get_set_operational_highlight_handler = _provider("app.modules.ticket_management.application.commands.set_operational_highlight.handler.SetOperationalHighlightHandler")

def get_change_priority_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
	from app.modules.ticket_management.application.commands.change_priority.handler import ChangePriorityHandler
	return ChangePriorityHandler(uow, publisher)

def get_add_ticket_attachment_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)], storage_service: Annotated[StorageService, Depends(get_storage_service)]):
	from app.modules.ticket_management.application.commands.add_ticket_attachment.handler import AddTicketAttachmentHandler
	return AddTicketAttachmentHandler(uow, publisher, storage_service)

def get_add_comment_attachment_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)], storage_service: Annotated[StorageService, Depends(get_storage_service)]):
	from app.modules.ticket_management.application.commands.add_comment_attachment.handler import AddCommentAttachmentHandler
	return AddCommentAttachmentHandler(uow, publisher, storage_service)

def get_download_attachment_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)], storage_service: Annotated[StorageService, Depends(get_storage_service)]):
	from app.modules.ticket_management.application.queries.download_attachment.handler import DownloadAttachmentHandler
	return DownloadAttachmentHandler(repository, storage_service)

def get_get_ticket_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)], users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]):
	from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
	return GetTicketHandler(repository, users)
def get_list_tickets_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)], users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]):
	from app.modules.ticket_management.application.queries.list_tickets.handler import ListTicketsHandler
	return ListTicketsHandler(repository, users)
def get_search_tickets_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)], users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]):
	from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
	return SearchTicketsHandler(repository, users)
def get_export_ticket_history_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)], users: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]):
	from app.modules.ticket_management.application.queries.export_ticket_history.handler import ExportTicketHistoryHandler
	return ExportTicketHistoryHandler(repository, users)

def _crud_provider(handler_name):
	def provider(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
		module = handler_name.rsplit('.', 1)[0]; cls = handler_name.rsplit('.', 1)[1]
		return getattr(__import__(module, fromlist=[cls]), cls)(uow, publisher)
	return provider

for _name in ("add_comment", "edit_comment", "delete_comment", "delete_ticket_attachment", "delete_comment_attachment", "archive_ticket", "restore_ticket"):
	globals()[f"get_{_name}_handler"] = _crud_provider(f"app.modules.ticket_management.application.commands.{_name}.handler.{''.join(part.title() for part in _name.split('_'))}Handler")
