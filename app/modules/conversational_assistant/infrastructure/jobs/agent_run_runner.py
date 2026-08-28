from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.modules.conversational_assistant.application.agent.context import build_llm_context
from app.modules.conversational_assistant.application.agent.resource_references import (
	resolve_ticket_references,
)
from app.modules.conversational_assistant.application.agent.system_prompt import compose_system_prompt
from app.modules.conversational_assistant.application.dto.message_dto import MessageDTO
from app.modules.conversational_assistant.application.interfaces.agent_run_runner import AgentRunRunner
from app.modules.conversational_assistant.application.tools.base import ToolContext
from app.modules.conversational_assistant.application.tools.registry import build_available_tools
from app.modules.conversational_assistant.domain.events.agent_run_completed import AgentRunCompleted
from app.modules.conversational_assistant.domain.exceptions import ConversationDomainError
from app.modules.conversational_assistant.domain.events.agent_run_failed import AgentRunFailed
from app.modules.conversational_assistant.infrastructure.agent.graph import build_agent_graph
from app.modules.conversational_assistant.infrastructure.delivery.agent_run_connection_manager import (
	agent_run_connection_manager,
)
from app.modules.conversational_assistant.infrastructure.jobs.current_user_rebuilder import rebuild_current_user
from app.modules.conversational_assistant.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.conversational_assistant.infrastructure.providers.ollama_llm_provider import OllamaLLMProvider
from app.shared.ai.llm_provider import ChatMessage
from app.shared.database.session import create_session
from app.shared.events.event import DomainEvent
from app.shared.events.event_publisher import EventPublisher
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry

logger = logging.getLogger(__name__)

_GENERIC_FAILURE_REASON = "L'assistant n'a pas pu répondre à ce message. Vous pouvez réessayer."


class ConversationalAgentRunner(AgentRunRunner):
	"""Composes and runs one agent turn -- the Infrastructure counterpart of Knowledge Base's
	SimilarityRecalculationRunner. Everything about *how* a turn is authorized and computed lives
	here; SendMessageHandler, which enqueues a call to `run`, knows none of it.

	Unlike the recalculation runner there is no single-flight flag: runs for different
	conversations are independent and may proceed concurrently without issue -- the constraint
	that needed one there (one whole-corpus rebuild at a time) has no counterpart here.
	"""

	def __init__(self) -> None:
		self._event_publisher: EventPublisher | None = None
		self._instance_authorization_registry: InstanceAuthorizationRegistry | None = None
		# No I/O in construction, matching EmbeddingProvider's own contract: ollama.AsyncClient's
		# constructor only builds an HTTP client, it does not connect.
		self._llm_provider = OllamaLLMProvider.from_settings()

	def bind(
		self, *, event_publisher: EventPublisher, instance_authorization_registry: InstanceAuthorizationRegistry,
	) -> None:
		"""Given at startup, not construction: this is a process-wide singleton created at import
		time, before the event bus or the instance-authorization registry exist. Both are handed
		over once bootstrap.register_subscriptions runs -- the same moment Knowledge Base's own
		runner is given its publisher."""
		self._event_publisher = event_publisher
		self._instance_authorization_registry = instance_authorization_registry

	async def run(self, *, conversation_id: UUID, run_id: UUID) -> None:
		session = create_session()
		try:
			uow = SqlAlchemyUnitOfWork(session)
			conversation = await uow.conversations.get(conversation_id)
			if conversation is None:
				# Nothing to mark, and nothing to record a failure against either -- _record_failure
				# would reload the same missing row. Only reachable if the conversation vanished
				# between the accepted request and this job.
				logger.error("Agent run %s: conversation %s no longer exists.", run_id, conversation_id)
				return
			conversation.mark_run_running(run_id=run_id, at=datetime.now(UTC))
			# Committed early so a client polling GET .../messages sees RUNNING promptly, without
			# waiting for the whole turn.
			await uow.conversations.save(conversation)
			await uow.commit()

			current_user = await rebuild_current_user(conversation.user_id, session)
			tools = build_available_tools(current_user)
			context = build_llm_context(conversation.messages)
			system_prompt = compose_system_prompt(current_user)
			tool_context = ToolContext(
				current_user=current_user,
				session_factory=create_session,
				instance_authorization_registry=self._require_instance_authorization_registry(),
			)
			graph = build_agent_graph(self._llm_provider, tools, tool_context)

			initial_state = {
				"messages": [ChatMessage(role="system", content=system_prompt), *context],
				"tool_calls_made": [],
				"iterations": 0,
			}

			final_state = None
			async for mode, chunk in graph.astream(initial_state, stream_mode=["custom", "values"]):
				if mode == "custom":
					if chunk["type"] == "message_delta":
						agent_run_connection_manager.publish_delta(run_id, chunk["content"])
					elif chunk["type"] == "tool_call":
						agent_run_connection_manager.publish_tool_call(run_id, chunk["name"], chunk["status"])
				else:  # mode == "values": the running state after each node; the last one is final
					final_state = chunk

			if not final_state or not final_state["messages"]:
				raise RuntimeError("Agent graph produced no final state.")

			answer = final_state["messages"][-1].content
			if not answer.strip():
				# Caught here rather than left to Message.create's EmptyMessageContent, which
				# reports an empty *domain* message and says nothing about the model having
				# returned nothing. A turn with no text and no tool call is a failed turn.
				raise RuntimeError(
					f"The model returned an empty final message after {final_state['iterations']} "
					f"iteration(s) and {len(final_state['tool_calls_made'])} tool call(s)."
				)
			# Before the answer becomes a stored Message, never after: a Message is final the moment
			# it exists, so this is the last point at which a link the run cannot vouch for can
			# still be taken out. The deltas already streamed carry the model's raw text, which is
			# why message_complete ships the whole validated answer -- the client replaces what it
			# rendered live with this one.
			answer = resolve_ticket_references(answer, final_state["tool_calls_made"])
			response_message = conversation.complete_run(
				run_id=run_id, response_message_id=uuid4(), content=answer,
				tool_invocations=final_state["tool_calls_made"], completed_at=datetime.now(UTC),
			)
			await uow.conversations.save(conversation)
			await uow.commit()
			await self._publish(
				AgentRunCompleted(
					conversation_id=conversation_id, run_id=run_id,
					response_message_id=response_message.id,
					tool_call_count=len(final_state["tool_calls_made"]),
					occurred_at=datetime.now(UTC), actor_id=None,
				)
			)
			agent_run_connection_manager.publish_completed(run_id, MessageDTO.from_message(response_message))
		except asyncio.CancelledError:
			# Shutdown in flight -- respect it immediately, no further DB writes (accepted v1
			# limitation: no broker, no resume; see app/workers/'s own documented contract).
			raise
		except Exception as exc:
			logger.exception("Agent run %s failed.", run_id)
			await self._record_failure(conversation_id, run_id, exc)
		finally:
			await session.close()

	async def _record_failure(self, conversation_id: UUID, run_id: UUID, exc: Exception) -> None:
		"""Opens its own fresh session rather than reusing the caller's: whatever raised may have
		left the main session's transaction unusable (the exception could *be* a failed commit).
		This is exactly the logic that cannot live in app/workers/handlers.py's generic
		log-and-swallow wrapper -- that wrapper has no concept of "run" and never even sees this
		exception, since this method catches it first."""
		session = create_session()
		try:
			uow = SqlAlchemyUnitOfWork(session)
			conversation = await uow.conversations.get(conversation_id)
			if conversation is None:
				return
			try:
				conversation.fail_run(
					run_id=run_id, failure_reason=_GENERIC_FAILURE_REASON,
					failure_detail=f"{type(exc).__name__}: {exc}", completed_at=datetime.now(UTC),
				)
			except ConversationDomainError:
				# The run is not in a state that can fail -- it was never started, or it already
				# completed and the exception came from the announcing that followed. Recording
				# the run is all this method exists to do, so there is nothing left to try; the
				# original failure is already logged by the caller. Raising here would replace it
				# with a second, less informative one, which is what used to happen.
				logger.exception("Agent run %s could not be recorded as failed.", run_id)
				return
			await uow.conversations.save(conversation)
			await uow.commit()
		finally:
			await session.close()

		await self._publish(
			AgentRunFailed(
				conversation_id=conversation_id, run_id=run_id, failure_reason=_GENERIC_FAILURE_REASON,
				occurred_at=datetime.now(UTC), actor_id=None,
			)
		)
		agent_run_connection_manager.publish_failed(run_id, _GENERIC_FAILURE_REASON)

	def _require_instance_authorization_registry(self) -> InstanceAuthorizationRegistry:
		if self._instance_authorization_registry is None:
			raise RuntimeError("ConversationalAgentRunner.bind() was never called.")
		return self._instance_authorization_registry

	async def _publish(self, event: DomainEvent) -> None:
		"""Announce an outcome, if there is anywhere to announce it to -- same guard as Knowledge
		Base's own runner, and for the same reason: the bus logs a failing subscriber and carries
		on, so this stays a plain call with no error handling of its own to be wrong about."""
		if self._event_publisher is None:
			return
		await self._event_publisher.publish(event)


# One per process, mirroring similarity_recalculation_runner: bound at startup, never per-request.
agent_run_runner = ConversationalAgentRunner()
