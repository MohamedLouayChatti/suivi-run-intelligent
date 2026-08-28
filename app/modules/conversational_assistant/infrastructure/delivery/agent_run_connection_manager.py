from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

from app.modules.conversational_assistant.application.dto.message_dto import MessageDTO


class AgentRunConnectionManager:
	"""In-process registry of live SSE connections, keyed by run_id -- not by user_id like
	Notifications' own manager, since the frontend already knows the exact run it is watching
	from the 202 response, and a run resolves exactly once (unlike an open-ended per-user feed).

	Single-process, in-memory -- same constraint every other part of this system's event
	delivery already has. If nobody is connected to a given run_id when a publish_* method is
	called, the call is a no-op past an empty queue list: no buffering or replay. That is an
	accepted v1 limitation (see infrastructure/agent/graph.py's own note) -- a client that
	(re)connects mid-run only sees events from that point on, and relies on
	GET .../messages for the authoritative catch-up, never on replay.
	"""

	def __init__(self) -> None:
		self._connections: dict[UUID, list[asyncio.Queue[dict[str, Any]]]] = {}

	def connect(self, run_id: UUID) -> asyncio.Queue[dict[str, Any]]:
		queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
		self._connections.setdefault(run_id, []).append(queue)
		return queue

	def disconnect(self, run_id: UUID, queue: asyncio.Queue[dict[str, Any]]) -> None:
		queues = self._connections.get(run_id)
		if not queues:
			return
		try:
			queues.remove(queue)
		except ValueError:
			return
		if not queues:
			del self._connections[run_id]

	def publish_delta(self, run_id: UUID, content: str) -> None:
		self._publish(run_id, event="message_delta", data={"content": content})

	def publish_tool_call(self, run_id: UUID, name: str, status: str) -> None:
		self._publish(run_id, event="tool_call", data={"name": name, "status": status})

	def publish_title(self, run_id: UUID, conversation_id: UUID, title: str) -> None:
		"""The conversation's generated title, pushed down the stream the client already has open.

		Not a terminal event, and not part of the run: title generation is its own background job,
		started by the same request and finished independently. The run stream carries it only
		because it is the connection the client is already holding -- keyed by run_id like every
		other event here, while the payload names the conversation the title belongs to, since that
		is what the client updates.

		It therefore arrives, or does not, on its own schedule: in practice well before the run
		resolves (one short call, no tools, against a whole agent turn), but a title finishing after
		the terminal event finds the stream closed and is published to nobody. Nothing is lost --
		the title is already stored, and the conversation list is the reconciliation path, exactly
		as GET .../messages is for a run.
		"""
		self._publish(
			run_id,
			event="conversation_title",
			data={"conversation_id": str(conversation_id), "title": title},
		)

	def publish_completed(self, run_id: UUID, message: MessageDTO) -> None:
		self._publish(run_id, event="message_complete", data=message)

	def publish_failed(self, run_id: UUID, failure_reason: str) -> None:
		self._publish(
			run_id, event="run_failed", data={"run_id": str(run_id), "failure_reason": failure_reason},
		)

	def _publish(self, run_id: UUID, *, event: str, data: Any) -> None:
		for queue in self._connections.get(run_id, []):
			queue.put_nowait({"event": event, "data": data})


agent_run_connection_manager = AgentRunConnectionManager()
