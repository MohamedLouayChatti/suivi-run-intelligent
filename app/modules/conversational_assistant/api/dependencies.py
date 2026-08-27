from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request

from app.modules.conversational_assistant.application.commands.create_conversation.handler import (
	CreateConversationHandler,
)
from app.modules.conversational_assistant.application.commands.send_message.handler import SendMessageHandler
from app.modules.conversational_assistant.application.queries.get_conversation_messages.handler import (
	GetConversationMessagesHandler,
)
from app.modules.conversational_assistant.application.queries.list_conversations.handler import (
	ListConversationsHandler,
)
from app.modules.conversational_assistant.infrastructure.events.in_memory_event_publisher import (
	InMemoryEventPublisher,
)
from app.modules.conversational_assistant.infrastructure.jobs.agent_run_runner import agent_run_runner
from app.modules.conversational_assistant.infrastructure.persistence.repositories.sqlalchemy_conversation_read_repository import (
	SqlAlchemyConversationReadRepository,
)
from app.modules.conversational_assistant.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.database.session import create_session
from app.workers.jobs import JobQueue
from app.workers.worker import job_queue as _job_queue


async def get_unit_of_work() -> AsyncIterator[SqlAlchemyUnitOfWork]:
	uow = SqlAlchemyUnitOfWork()
	try:
		yield uow
	finally:
		await uow.close()


async def get_read_repository() -> AsyncIterator[SqlAlchemyConversationReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyConversationReadRepository(session)
	finally:
		await session.close()


def get_event_publisher(request: Request) -> InMemoryEventPublisher:
	return InMemoryEventPublisher(request.app.state.event_bus)


def get_job_queue() -> JobQueue:
	return _job_queue


def get_create_conversation_handler(
	uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
) -> CreateConversationHandler:
	return CreateConversationHandler(uow)


def get_send_message_handler(
	uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)],
	publisher: Annotated[InMemoryEventPublisher, Depends(get_event_publisher)],
	queue: Annotated[JobQueue, Depends(get_job_queue)],
) -> SendMessageHandler:
	# agent_run_runner is a process-wide singleton (mirrors similarity_recalculation_runner),
	# injected directly rather than through Depends since it is not request-scoped.
	return SendMessageHandler(uow, publisher, queue, agent_run_runner)


def get_get_conversation_messages_handler(
	repository: Annotated[SqlAlchemyConversationReadRepository, Depends(get_read_repository)],
) -> GetConversationMessagesHandler:
	return GetConversationMessagesHandler(repository)


def get_list_conversations_handler(
	repository: Annotated[SqlAlchemyConversationReadRepository, Depends(get_read_repository)],
) -> ListConversationsHandler:
	return ListConversationsHandler(repository)
