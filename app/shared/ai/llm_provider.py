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
	role: Literal["system", "user", "assistant", "tool"]
	content: str
	tool_call_id: str | None = None
	tool_calls: tuple[ToolCallRequest, ...] = ()


@dataclass(frozen=True, slots=True)
class ChatDelta:
	"""One incremental chunk of a streamed chat turn.

	`content` is the text fragment carried by this chunk, empty if this chunk carries none.
	`tool_calls` is populated only on the final chunk (`done=True`), if the model is invoking
	tools for this turn -- providers report tool calls as a completed structured field rather
	than incrementally, unlike prose content.
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
		"""One LLM turn, yielded incrementally. The final yielded ChatDelta has done=True and
		carries the complete tool_calls tuple, if the model is invoking any."""
		raise NotImplementedError
