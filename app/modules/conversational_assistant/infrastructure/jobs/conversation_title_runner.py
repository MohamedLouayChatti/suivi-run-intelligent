from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.modules.conversational_assistant.application.interfaces.conversation_title_runner import (
	ConversationTitleRunner,
)
from app.modules.conversational_assistant.domain.entities.conversation import normalize_title
from app.modules.conversational_assistant.infrastructure.delivery.agent_run_connection_manager import (
	agent_run_connection_manager,
)
from app.modules.conversational_assistant.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.conversational_assistant.infrastructure.providers.ollama_title_generator import (
	OllamaTitleGenerator,
)
from app.shared.database.session import create_session

logger = logging.getLogger(__name__)


class BackgroundConversationTitleRunner(ConversationTitleRunner):
	"""Names one conversation from its first message -- the Infrastructure counterpart of
	ConversationalAgentRunner, and deliberately a fraction of its size.

	It is not a node in the agent graph and not an agent of its own: naming a conversation depends
	on the question, never on the answer, so there is nothing here to sequence against the run. The
	two jobs are enqueued by the same request and proceed independently.

	No single-flight flag and no failure state, unlike its neighbour. Titles for different
	conversations are independent, and a conversation is only ever titled once -- on its first
	message, by the one request that observes the conversation as untitled.
	"""

	def __init__(self) -> None:
		# No I/O in construction: this is a module-level singleton built at import time, and
		# ollama.AsyncClient's constructor only builds an HTTP client. Same contract the agent
		# runner's own provider is held to.
		self._generator = OllamaTitleGenerator.from_settings()

	async def run(self, *, conversation_id: UUID, run_id: UUID, first_message: str) -> None:
		try:
			raw = await self._generator.generate(first_message)
		except asyncio.CancelledError:
			# Shutdown in flight. Respected immediately, with no write attempted -- the interim
			# title stands, which is exactly the outcome a failure produces anyway.
			raise
		except Exception:
			logger.warning(
				"Title generation for conversation %s failed; its interim title stands.",
				conversation_id, exc_info=True,
			)
			return

		title = normalize_title(raw)
		if title is None:
			# The model answered, but with nothing a title can be made of. Logged at warning like a
			# provider failure, because from here the two are the same event: no title was
			# obtained. The raw answer is included -- it is the only way to tell a prompt that
			# needs work from an endpoint that is down.
			logger.warning(
				"Title generation for conversation %s produced no usable title from %r.",
				conversation_id, raw,
			)
			return

		# Opened only now, and held for one statement. The session deliberately does not span the
		# model call: that call takes about a second, and a database session held open across it
		# would be idle in a transaction for the whole of it, for a write that touches one column.
		session = create_session()
		try:
			uow = SqlAlchemyUnitOfWork(session)
			await uow.conversations.set_title(conversation_id, title)
			await uow.commit()
		except Exception:
			logger.warning(
				"Generated title for conversation %s could not be stored; its interim title stands.",
				conversation_id, exc_info=True,
			)
			return
		finally:
			await session.close()

		# After the commit, never before: the client is told about a title that is already durable,
		# so a browser and the conversations list can never disagree about what the conversation is
		# called. The same ordering every handler in this codebase publishes its events with.
		agent_run_connection_manager.publish_title(run_id, conversation_id, title)


# One per process, mirroring agent_run_runner: created at import time, never per-request. Nothing to
# bind at startup, unlike the agent runner -- this job publishes no domain event and authorizes
# nothing, so it needs neither an event publisher nor the instance-authorization registry.
conversation_title_runner = BackgroundConversationTitleRunner()
