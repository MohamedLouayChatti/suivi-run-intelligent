from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request

from app.modules.ticket_management.application.commands.add_comment.handler import AddCommentHandler
from app.modules.ticket_management.application.commands.add_ticket_attachment.handler import AddTicketAttachmentHandler
from app.modules.ticket_management.application.commands.archive_ticket.handler import ArchiveTicketHandler
from app.modules.ticket_management.application.commands.assign_ticket.handler import AssignTicketHandler
from app.modules.ticket_management.application.commands.change_priority.handler import ChangePriorityHandler
from app.modules.ticket_management.application.commands.change_status.handler import ChangeStatusHandler
from app.modules.ticket_management.application.commands.create_ticket.handler import CreateTicketHandler
from app.modules.ticket_management.application.commands.delete_comment.handler import DeleteCommentHandler
from app.modules.ticket_management.application.commands.delete_ticket_attachment.handler import DeleteTicketAttachmentHandler
from app.modules.ticket_management.application.commands.edit_comment.handler import EditCommentHandler
from app.modules.ticket_management.application.commands.restore_ticket.handler import RestoreTicketHandler
from app.modules.ticket_management.application.commands.transfer_application.handler import TransferApplicationHandler
from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
from app.modules.ticket_management.application.queries.list_tickets.handler import ListTicketsHandler
from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import SqlAlchemyTicketReadRepository
from app.modules.ticket_management.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.database.session import create_session
from app.shared.events.event_bus import InMemoryEventBus


async def get_unit_of_work() -> AsyncIterator[SqlAlchemyUnitOfWork]:
	uow = SqlAlchemyUnitOfWork()
	try:
		yield uow
	finally:
		await uow.close()


async def get_read_repository() -> AsyncIterator[SqlAlchemyTicketReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyTicketReadRepository(session)
	finally:
		await session.close()


def get_event_publisher(request: Request) -> InMemoryEventPublisher:
	event_bus: InMemoryEventBus = request.app.state.event_bus
	return InMemoryEventPublisher(event_bus)


def get_create_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> CreateTicketHandler:
	return CreateTicketHandler(uow, publisher)


def get_assign_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> AssignTicketHandler:
	return AssignTicketHandler(uow, publisher)


def get_change_priority_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> ChangePriorityHandler:
	return ChangePriorityHandler(uow, publisher)


def get_change_status_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> ChangeStatusHandler:
	return ChangeStatusHandler(uow, publisher)


def get_transfer_application_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> TransferApplicationHandler:
	return TransferApplicationHandler(uow, publisher)


def get_add_comment_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> AddCommentHandler:
	return AddCommentHandler(uow, publisher)


def get_edit_comment_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> EditCommentHandler:
	return EditCommentHandler(uow, publisher)


def get_delete_comment_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> DeleteCommentHandler:
	return DeleteCommentHandler(uow, publisher)


def get_add_ticket_attachment_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> AddTicketAttachmentHandler:
	return AddTicketAttachmentHandler(uow, publisher)


def get_delete_ticket_attachment_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> DeleteTicketAttachmentHandler:
	return DeleteTicketAttachmentHandler(uow, publisher)


def get_archive_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> ArchiveTicketHandler:
	return ArchiveTicketHandler(uow, publisher)


def get_restore_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]) -> RestoreTicketHandler:
	return RestoreTicketHandler(uow, publisher)


def get_get_ticket_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)]) -> GetTicketHandler:
	return GetTicketHandler(repository)


def get_list_tickets_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)]) -> ListTicketsHandler:
	return ListTicketsHandler(repository)


def get_search_tickets_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)]) -> SearchTicketsHandler:
	return SearchTicketsHandler(repository)
