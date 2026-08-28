from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.sse import EventSourceResponse, ServerSentEvent

from app.modules.conversational_assistant.api import dependencies as dep
from app.modules.conversational_assistant.api.schemas.message import MessageResponse
from app.modules.conversational_assistant.application.dto.run_replay_dto import RunReplayDTO
from app.modules.conversational_assistant.application.interfaces.conversation_read_repository import (
	ConversationReadRepository,
)
from app.modules.conversational_assistant.domain.enums.run_status import RunStatus
from app.modules.conversational_assistant.infrastructure.delivery.agent_run_connection_manager import (
	agent_run_connection_manager,
)
from app.shared.security.instance_permissions import require_instance_permission
from app.shared.security.permissions import require_permissions

_TERMINAL_EVENTS = frozenset({"message_complete", "run_failed"})

# Emitted when a run resolved before this client connected but left no message to replay -- a
# FAILED run whose failure_reason was never persisted, or a run id that matches no row at all.
_UNRESOLVABLE_RUN_REASON = "L'assistant n'a pas pu répondre à ce message. Vous pouvez réessayer."

sse_router = APIRouter(prefix="/conversational-assistant", tags=["conversational-assistant"])


def _replay_events(replay: RunReplayDTO | None) -> list[ServerSentEvent]:
	"""The terminal event a settled run would have streamed, rebuilt from stored state.

	A completed run replays its message; anything else that can no longer produce one -- a failed
	run, or a run id with no row behind it -- replays a failure. Returning a failure for an unknown
	id rather than nothing is deliberate: this endpoint has no handler downstream to raise a
	not-found, so the alternative is an open connection waiting on a run that will never report.
	"""
	if replay is not None and replay.status is RunStatus.COMPLETED and replay.response_message is not None:
		return [
			ServerSentEvent(
				data=MessageResponse.from_dto(replay.response_message), event="message_complete",
			)
		]
	run_id = "" if replay is None else str(replay.run_id)
	reason = (replay.failure_reason if replay else None) or _UNRESOLVABLE_RUN_REASON
	return [ServerSentEvent(data={"run_id": run_id, "failure_reason": reason}, event="run_failed")]


@sse_router.get(
	"/runs/{run_id}/stream",
	response_class=EventSourceResponse,
	dependencies=[
		Depends(require_permissions("conversational_assistant.use")),
		Depends(require_instance_permission("agent_run", "read", path_param="run_id")),
	],
)
async def stream_agent_run(
	run_id: UUID,
	conversations: Annotated[ConversationReadRepository, Depends(dep.get_read_repository)],
) -> AsyncIterable[ServerSentEvent]:
	"""Live delivery of one agent run: `message_delta`/`tool_call` events while it is in flight,
	then exactly one terminal event (`message_complete` or `run_failed`) before closing -- a run
	resolves once, unlike Notifications' open-ended per-user feed.

	One event on this stream is not about the run: `conversation_title` carries the title generated
	for a conversation by its own background job, which the same request started and which finishes
	independently. It rides here because this is the connection the client already holds, and it
	needs no handling of its own below -- a non-terminal event is forwarded as it stands. A title
	that lands after the terminal event is simply not delivered; it is already stored, and the
	conversation list is what reconciles it, exactly as GET .../messages does for a run.

	Auth stays header-based (Authorization: Bearer), same as every other route -- the frontend
	needs the existing fetch-based SSE client, not the native browser EventSource API, which
	cannot set that header.

	The run is enqueued by the POST that returned this run_id, so it is already in flight before
	this request arrives and may even have finished: the connection manager buffers nothing, so a
	terminal event published to an empty subscriber list is gone for good. The subscription is
	therefore taken out *before* stored state is read, never after -- reading first would leave a
	gap in which a run could resolve unobserved by both halves. Once subscribed, a run already
	settled in the database is answered from that state and the stream closes immediately.

	Deltas emitted before this connection are still not replayed; `message_complete` always
	carries the full text, and GET .../messages remains the reconciliation path.
	"""
	queue = agent_run_connection_manager.connect(run_id)
	try:
		replay = await conversations.get_run_replay(run_id)
		if replay is None or replay.is_terminal:
			for event in _replay_events(replay):
				yield event
			return

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
