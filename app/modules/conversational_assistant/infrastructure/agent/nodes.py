from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from langgraph.config import get_stream_writer

from app.modules.conversational_assistant.application.tools.base import (
	ToolArgumentError,
	ToolContext,
	ToolSpec,
)
from app.modules.conversational_assistant.domain.entities.tool_invocation import ToolInvocation
from app.modules.conversational_assistant.infrastructure.agent.state import AgentState
from app.shared.ai.llm_provider import ChatMessage, LLMProvider, ToolSchema

logger = logging.getLogger(__name__)

# How many tool-calling turns the agent may take before it is made to answer with what it has.
# Not a failure threshold: reaching it costs the model its remaining tool calls, never the user
# their answer (see _FINAL_TURN_INSTRUCTION). Sized for the longest legitimate chain the catalogue
# supports -- enumerate a team, read several colleagues' figures, then their tickets -- with room
# for the occasional corrective retry on top.
MAX_TOOL_ITERATIONS = 12

# Appended for the one forced turn that follows the cap. The model is told plainly that it has run
# out of tool calls rather than left to wonder why they stopped working, because an answer that
# silently omits what it could not reach is worse than one that says so.
_FINAL_TURN_INSTRUCTION = (
	"Vous avez atteint le nombre maximum d'appels d'outils pour ce message. Répondez maintenant, "
	"en français, avec les seules informations déjà récupérées. Si elles ne suffisent pas, "
	"dites-le et proposez une question plus précise à l'utilisateur."
)


def build_agent_node(llm_provider: LLMProvider, tool_specs: Sequence[ToolSpec]):
	"""One node: call the model, forward every content delta live, stop once it has answered
	without requesting more tools. Streams uniformly regardless of whether this turn ultimately
	requests a tool -- see LLMProvider's own "one method, not two" note for why that distinction
	is unnecessary.

	Past MAX_TOOL_ITERATIONS the turn runs with no tools offered at all and any tool call is
	discarded, so this node always terminates: the graph's router sees a message with no tool
	calls and ends. Exceeding the cap used to raise instead, which threw away every tool result
	the run had already paid for and left the user a generic failure -- a budget the agent overran
	is a reason to stop searching, not a reason to have nothing to say.
	"""
	tool_schemas = [
		ToolSchema(name=spec.name, description=spec.description, parameters=spec.json_schema())
		for spec in tool_specs
	]

	async def agent_node(state: AgentState) -> AgentState:
		is_final_turn = state["iterations"] >= MAX_TOOL_ITERATIONS
		messages = state["messages"]
		if is_final_turn:
			logger.warning(
				"Agent reached %s tool iterations; answering with what it has.", MAX_TOOL_ITERATIONS
			)
			messages = [*messages, ChatMessage(role="system", content=_FINAL_TURN_INSTRUCTION)]

		writer = get_stream_writer()
		content_parts: list[str] = []
		tool_calls: tuple = ()
		async for delta in llm_provider.stream_chat(
			messages=messages, tools=() if is_final_turn else tool_schemas
		):
			if delta.content:
				content_parts.append(delta.content)
				writer({"type": "message_delta", "content": delta.content})
			# Captured from whichever chunk carries them, not from the `done` chunk: a provider is
			# free to emit them earlier, and Ollama does (see ChatDelta's contract).
			if delta.tool_calls:
				tool_calls = delta.tool_calls

		message = ChatMessage(
			role="assistant",
			content="".join(content_parts),
			# Dropped rather than honoured on the final turn: no tool was offered, so a call is the
			# model ignoring that, and running it would route straight back into the loop for good.
			tool_calls=() if is_final_turn else tool_calls,
		)
		return {
			# The forced instruction is deliberately not carried into the returned state: it
			# belongs to this one turn, and persisting it would keep telling every later turn of a
			# longer conversation that its tools are exhausted.
			"messages": [*state["messages"], message],
			"tool_calls_made": state["tool_calls_made"],
			"iterations": state["iterations"] + 1,
		}

	return agent_node


def build_tools_node(tool_specs: Sequence[ToolSpec], tool_context: ToolContext):
	"""One node: execute every tool call the last agent turn requested.

	A tool failure -- unknown tool, invalid arguments, authorization denial, not-found -- does
	NOT abort the run. It is fed back as an ordinary role="tool" message so the model can recover
	or apologize; only a genuine infrastructure failure (raised out of `spec.execute` itself, e.g.
	the LLM/DB being unreachable) propagates and fails the whole run.
	"""
	specs_by_name = {spec.name: spec for spec in tool_specs}

	async def tools_node(state: AgentState) -> AgentState:
		writer = get_stream_writer()
		last_message = state["messages"][-1]
		tool_messages: list[ChatMessage] = []
		recorded: list[ToolInvocation] = list(state["tool_calls_made"])

		for call in last_message.tool_calls:
			started_at = datetime.now(UTC)
			writer({"type": "tool_call", "name": call.name, "status": "started"})
			spec = specs_by_name.get(call.name)

			if spec is None:
				error = f"Outil inconnu : {call.name}."
				tool_messages.append(
					ChatMessage(role="tool", content=error, tool_call_id=call.id, tool_name=call.name)
				)
				recorded.append(
					ToolInvocation.failed(
						id=uuid4(), tool_name=call.name, arguments=call.arguments, error=error,
						started_at=started_at, completed_at=datetime.now(UTC),
					)
				)
				writer({"type": "tool_call", "name": call.name, "status": "failed"})
				continue

			try:
				validated_args = spec.validate_arguments(call.arguments)
			except ToolArgumentError as exc:
				# Names the offending field and its legal values, so the model can correct the call
				# on its next turn instead of re-guessing until the iteration budget runs out.
				error = str(exc)
				tool_messages.append(
					ChatMessage(role="tool", content=error, tool_call_id=call.id, tool_name=call.name)
				)
				recorded.append(
					ToolInvocation.failed(
						id=uuid4(), tool_name=call.name, arguments=call.arguments, error=error,
						started_at=started_at, completed_at=datetime.now(UTC),
					)
				)
				writer({"type": "tool_call", "name": call.name, "status": "failed"})
				continue

			result = await spec.execute(validated_args, tool_context)
			completed_at = datetime.now(UTC)
			if result.ok:
				tool_messages.append(
					ChatMessage(
						# ensure_ascii=False keeps accented French readable (and cheaper) rather than
						# \uXXXX-escaped; default=str is a safety net so one stray non-JSON-native
						# value degrades that field instead of raising out of this node and failing
						# the whole run.
						role="tool", content=json.dumps(result.payload, ensure_ascii=False, default=str),
						tool_call_id=call.id, tool_name=call.name,
					)
				)
				recorded.append(
					ToolInvocation.succeeded(
						id=uuid4(), tool_name=call.name, arguments=call.arguments,
						result=result.payload or {}, started_at=started_at, completed_at=completed_at,
					)
				)
				writer({"type": "tool_call", "name": call.name, "status": "completed"})
			else:
				tool_messages.append(
					ChatMessage(
						role="tool", content=result.error or "", tool_call_id=call.id, tool_name=call.name,
					)
				)
				recorded.append(
					ToolInvocation.failed(
						id=uuid4(), tool_name=call.name, arguments=call.arguments,
						error=result.error or "", started_at=started_at, completed_at=completed_at,
					)
				)
				writer({"type": "tool_call", "name": call.name, "status": "failed"})

		return {
			"messages": [*state["messages"], *tool_messages],
			"tool_calls_made": recorded,
			"iterations": state["iterations"],
		}

	return tools_node
