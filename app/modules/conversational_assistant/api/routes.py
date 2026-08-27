from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status

from app.api.pagination import PagedResponse
from app.modules.conversational_assistant.api import dependencies as dep
from app.modules.conversational_assistant.api.schemas.conversation import (
	ConversationSummaryResponse,
	CreateConversationResponse,
)
from app.modules.conversational_assistant.api.schemas.message import (
	ConversationMessagesResponse,
	SendMessageRequest,
	SendMessageResponse,
)
from app.modules.conversational_assistant.application.commands.create_conversation.command import (
	CreateConversationCommand,
)
from app.modules.conversational_assistant.application.commands.send_message.command import SendMessageCommand
from app.modules.conversational_assistant.application.queries.get_conversation_messages.query import (
	GetConversationMessagesQuery,
)
from app.modules.conversational_assistant.application.queries.list_conversations.query import (
	ListConversationsQuery,
)
from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.instance_permissions import require_instance_permission
from app.shared.security.permissions import require_permissions

router = APIRouter(prefix="/conversational-assistant", tags=["conversational-assistant"])
now = lambda: datetime.now(UTC)


@router.post(
	"/conversations",
	response_model=CreateConversationResponse,
	status_code=status.HTTP_201_CREATED,
	dependencies=[Depends(require_permissions("conversational_assistant.use"))],
)
async def create_conversation(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_create_conversation_handler),
):
	result = await handler.handle(
		CreateConversationCommand(conversation_id=uuid4(), user_id=current_user.id, created_at=now())
	)
	return CreateConversationResponse.from_dto(result)


@router.get(
	"/conversations",
	response_model=PagedResponse[ConversationSummaryResponse],
	dependencies=[Depends(require_permissions("conversational_assistant.use"))],
)
async def list_conversations(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_list_conversations_handler),
	page: int = Query(1, ge=1),
	page_size: int = Query(50, ge=1, le=100),
):
	result = await handler.handle(
		ListConversationsQuery(user_id=current_user.id, limit=page_size, offset=(page - 1) * page_size)
	)
	return PagedResponse(
		items=[ConversationSummaryResponse.from_dto(conversation) for conversation in result.items],
		total=result.total,
	)


@router.post(
	"/conversations/{conversation_id}/messages",
	response_model=SendMessageResponse,
	status_code=status.HTTP_202_ACCEPTED,
	dependencies=[
		Depends(require_permissions("conversational_assistant.use")),
		Depends(require_instance_permission("conversation", "append", path_param="conversation_id")),
	],
)
async def send_message(
	conversation_id: UUID,
	payload: SendMessageRequest,
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_send_message_handler),
):
	"""202 Accepted with identifiers, not an empty body: unlike a fire-and-forget trigger, a
	Message row and a Run row were durably created in *this* request, and the frontend has an
	immediate need for `run_id` (to open the SSE stream) and `user_message_id`/`conversation_id`
	(to reconcile its own optimistic UI). The agent's reply is not computed here -- it is written
	later, from the background job this call enqueues."""
	result = await handler.handle(
		SendMessageCommand(
			conversation_id=conversation_id, message_id=uuid4(), run_id=uuid4(),
			content=payload.content, sent_at=now(), actor_id=current_user.id,
		)
	)
	return SendMessageResponse.from_dto(result)


@router.get(
	"/conversations/{conversation_id}/messages",
	response_model=ConversationMessagesResponse,
	dependencies=[
		Depends(require_permissions("conversational_assistant.use")),
		Depends(require_instance_permission("conversation", "read", path_param="conversation_id")),
	],
)
async def get_conversation_messages(
	conversation_id: UUID,
	handler=Depends(dep.get_get_conversation_messages_handler),
	page: int = Query(1, ge=1),
	page_size: int = Query(50, ge=1, le=200),
):
	result = await handler.handle(
		GetConversationMessagesQuery(conversation_id=conversation_id, limit=page_size, offset=(page - 1) * page_size)
	)
	return ConversationMessagesResponse.from_dto(result)
