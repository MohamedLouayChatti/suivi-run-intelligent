from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.modules.notifications.api.schemas import NotificationResponse
from app.modules.notifications.infrastructure.delivery.sse_connection_manager import connection_manager
from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.permissions import require_permissions

sse_router = APIRouter(prefix="/notifications", tags=["notifications"])


@sse_router.get("/stream", response_class=EventSourceResponse, dependencies=[Depends(require_permissions("notification.read"))])
async def stream_notifications(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> AsyncIterable[ServerSentEvent]:
	"""Live notification stream for the connected user only.

	Auth stays header-based (Authorization: Bearer, same as every other route) --
	the frontend must use a fetch-based SSE client instead of the native browser
	EventSource API, since that can't send an Authorization header.
	"""
	queue = connection_manager.connect(current_user.id)
	try:
		while True:
			notification = await queue.get()
			yield ServerSentEvent(data=NotificationResponse.from_dto(notification), event="notification")
	finally:
		connection_manager.disconnect(current_user.id, queue)
