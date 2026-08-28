from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class ConversationTitleRunner(ABC):
	"""Generates and stores the title of a conversation that has just received its first message.

	The same split as AgentRunRunner, for the same reason: SendMessageHandler enqueues a call to
	`run` and knows nothing about which model answers, how the call is made, or how the result
	reaches a browser -- all of that is Infrastructure's concern.

	Takes `first_message` rather than re-reading it: the handler that enqueues this has the text in
	hand, and passing it spares the job a query for a row it is about to update by id anyway.

	`run_id` is carried only so the finished title can be pushed down the SSE stream the client
	already has open for that run. It creates no dependency on the run's outcome -- this work is
	decoupled from the agent turn and neither waits for nor affects it.
	"""

	@abstractmethod
	async def run(self, *, conversation_id: UUID, run_id: UUID, first_message: str) -> None:
		"""Never raises. A title is cosmetic and an interim one is already stored, so a failure is
		logged and dropped rather than surfaced -- there is no caller left to report it to and
		nothing for a user to do about it."""
		raise NotImplementedError
