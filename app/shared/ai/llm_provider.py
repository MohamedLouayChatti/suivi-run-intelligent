from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True, slots=True)
class ToolCallRequest:
	"""One tool call the model is asking the agent loop to execute.

	`arguments` is untrusted: it is whatever the model produced, JSON-decoded and nothing more --
	the tool layer is what validates it against a schema before ever acting on it, never this port.
	`id` is local bookkeeping that correlates the eventual tool result message back to this
	specific call within one turn; not every provider supplies a stable one, so an adapter may
	need to synthesize it.
	"""

	id: str
	name: str
	arguments: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ToolSchema:
	"""One tool's LLM-facing definition -- name, description, and a JSON Schema for its
	arguments, built by each tool from its own Pydantic args model."""

	name: str
	description: str
	parameters: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ChatMessage:
	"""One message in a chat turn's context.

	A `role="tool"` message carries both `tool_call_id` and `tool_name`, because providers
	correlate a result back to its call differently: OpenAI-style APIs match on the call id,
	Ollama's chat API has no id field at all and matches on the tool's name. Carrying both keeps
	the port provider-agnostic -- each adapter forwards whichever its wire format actually has,
	and a result that identifies its tool by neither is one the model cannot interpret.
	"""

	role: Literal["system", "user", "assistant", "tool"]
	content: str
	tool_call_id: str | None = None
	tool_name: str | None = None
	tool_calls: tuple[ToolCallRequest, ...] = ()


@dataclass(frozen=True, slots=True)
class ChatDelta:
	"""One incremental chunk of a streamed chat turn.

	`content` is the text fragment carried by this chunk, empty if this chunk carries none.
	`tool_calls` is a *complete* set of calls, never a partial one -- providers report tool calls
	as a finished structured field rather than incrementally, unlike prose content. It is NOT
	guaranteed to land on the final chunk: Ollama, for one, emits the calls on their own chunk
	well before `done=True`. A consumer must therefore capture tool calls from whichever chunk
	carries them and must not read them off the `done` chunk alone.
	"""

	content: str
	done: bool
	tool_calls: tuple[ToolCallRequest, ...] = ()


class LLMProvider(ABC):
	"""Port for a chat-completions model capable of tool calling. Only Infrastructure implements
	this -- business logic never calls a provider (Ollama, Anthropic, etc.) directly, mirroring
	EmbeddingProvider's own separation.

	One method, not a streamed/non-streamed pair: a turn that ends up requesting tools typically
	carries little or no prose content anyway (the tool invocation is a structured field, not
	narrated text), so streaming every turn uniformly costs nothing extra and the agent loop
	never has to know in advance which turn will turn out to be the answering one.
	"""

	@property
	@abstractmethod
	def model_name(self) -> str:
		raise NotImplementedError

	async def warm_up(self) -> None:
		"""Resolve whatever the provider can only resolve after a network call, e.g. a model's
		build identity. Default no-op, overridable -- construction must do no I/O, and a long
		batch of calls should fail on its first turn rather than partway through, which is why
		this exists as its own step instead of hiding inside the first call. Same contract as
		EmbeddingProvider.warm_up()."""
		return None

	@abstractmethod
	def stream_chat(
		self, *, messages: Sequence[ChatMessage], tools: Sequence[ToolSchema]
	) -> AsyncIterator[ChatDelta]:
		"""One LLM turn, yielded incrementally. The final yielded ChatDelta has done=True; any
		tool calls the model is invoking arrive complete on whichever chunk carries them, which
		is not necessarily that last one."""
		raise NotImplementedError
