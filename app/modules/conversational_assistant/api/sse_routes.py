from __future__ import annotations

from collections.abc import AsyncIterable
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.modules.conversational_assistant.api.schemas.message import MessageResponse
from app.modules.conversational_assistant.infrastructure.delivery.agent_run_connection_manager import (
	agent_run_connection_manager,
)
from app.shared.security.instance_permissions import require_instance_permission
from app.shared.security.permissions import require_permissions

_TERMINAL_EVENTS = frozenset({"message_complete", "run_failed"})

sse_router = APIRouter(prefix="/conversational-assistant", tags=["conversational-assistant"])


@sse_router.get(
	"/runs/{run_id}/stream",
	response_class=EventSourceResponse,
	dependencies=[
		Depends(require_permissions("conversational_assistant.use")),
		Depends(require_instance_permission("agent_run", "read", path_param="run_id")),
	],
)
async def stream_agent_run(run_id: UUID) -> AsyncIterable[ServerSentEvent]:
	"""Live delivery of one agent run: `message_delta`/`tool_call` events while it is in flight,
	then exactly one terminal event (`message_complete` or `run_failed`) before closing -- a run
	resolves once, unlike Notifications' open-ended per-user feed.

	Auth stays header-based (Authorization: Bearer), same as every other route -- the frontend
	needs the existing fetch-based SSE client, not the native browser EventSource API, which
	cannot set that header.

	A client that (re)connects after some events have already been sent only receives events from
	that point on -- AgentRunConnectionManager does not replay a backlog (see its own docstring).
	This self-heals the moment the run finishes: `message_complete` always carries the full text,
	and GET .../messages is the reconciliation path for a client that misses this stream entirely.
	"""
	queue = agent_run_connection_manager.connect(run_id)
	try:
		while True:
			item = await queue.get()
			data = item["data"]
			if item["event"] == "message_complete":
				data = MessageResponse.from_dto(data)
			yield ServerSentEvent(data=data, event=item["event"])
			if item["event"] in _TERMINAL_EVENTS:
				break
	finally:
		agent_run_connection_manager.disconnect(run_id, queue)
