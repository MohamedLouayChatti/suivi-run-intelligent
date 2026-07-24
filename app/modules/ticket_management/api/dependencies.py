from collections.abc import AsyncIterator
from typing import Annotated
from fastapi import Depends, Request
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import SqlAlchemyTicketReadRepository
from app.modules.ticket_management.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.database.session import create_session
from app.shared.events.event_bus import InMemoryEventBus

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

def _command_handler(handler_type, uow, publisher): return handler_type(uow, publisher)

def get_create_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
	from app.modules.ticket_management.application.commands.create_ticket.handler import CreateTicketHandler
	return _command_handler(CreateTicketHandler, uow, publisher)

def get_reassign_ticket_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
	from app.modules.ticket_management.application.commands.reassign_ticket.handler import ReassignTicketHandler
	return _command_handler(ReassignTicketHandler, uow, publisher)

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
get_internal_transfer_ticket_handler = _provider("app.modules.ticket_management.application.commands.internal_transfer_ticket.handler.InternalTransferTicketHandler")
get_external_transfer_ticket_handler = _provider("app.modules.ticket_management.application.commands.external_transfer_ticket.handler.ExternalTransferTicketHandler")

def get_change_priority_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
	from app.modules.ticket_management.application.commands.change_priority.handler import ChangePriorityHandler
	return ChangePriorityHandler(uow, publisher)

def get_get_ticket_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)]):
	from app.modules.ticket_management.application.queries.get_ticket.handler import GetTicketHandler
	return GetTicketHandler(repository)
def get_list_tickets_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)]):
	from app.modules.ticket_management.application.queries.list_tickets.handler import ListTicketsHandler
	return ListTicketsHandler(repository)
def get_search_tickets_handler(repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_read_repository)]):
	from app.modules.ticket_management.application.queries.search_tickets.handler import SearchTicketsHandler
	return SearchTicketsHandler(repository)

def _crud_provider(handler_name):
	def provider(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)]):
		module = handler_name.rsplit('.', 1)[0]; cls = handler_name.rsplit('.', 1)[1]
		return getattr(__import__(module, fromlist=[cls]), cls)(uow, publisher)
	return provider

for _name in ("add_comment", "edit_comment", "delete_comment", "add_ticket_attachment", "delete_ticket_attachment", "archive_ticket", "restore_ticket"):
	globals()[f"get_{_name}_handler"] = _crud_provider(f"app.modules.ticket_management.application.commands.{_name}.handler.{''.join(part.title() for part in _name.split('_'))}Handler")
