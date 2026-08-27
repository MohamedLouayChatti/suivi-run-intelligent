from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from uuid import uuid4

from ollama import AsyncClient

from app.modules.conversational_assistant.infrastructure.providers.chat_model import CHAT_MODEL_TAG
from app.shared.ai.llm_provider import ChatDelta, ChatMessage, LLMProvider, ToolCallRequest, ToolSchema
from app.shared.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMProviderUnavailable(RuntimeError):
	"""Ollama could not be reached, or failed to open a chat stream."""


def _to_ollama_message(message: ChatMessage) -> dict:
	payload: dict = {"role": message.role, "content": message.content}
	if message.tool_call_id is not None:
		payload["tool_call_id"] = message.tool_call_id
	if message.tool_calls:
		payload["tool_calls"] = [
			{"function": {"name": call.name, "arguments": call.arguments}} for call in message.tool_calls
		]
	return payload


def _to_ollama_tool(tool: ToolSchema) -> dict:
	return {
		"type": "function",
		"function": {"name": tool.name, "description": tool.description, "parameters": tool.parameters},
	}


def _from_ollama_tool_calls(raw_tool_calls: object) -> tuple[ToolCallRequest, ...]:
	if not raw_tool_calls:
		return ()
	calls: list[ToolCallRequest] = []
	for raw_call in raw_tool_calls:
		function = raw_call.function
		# Ollama's tool-call responses don't reliably carry a stable id (unlike OpenAI's) -- a
		# local one is synthesized here, used only to correlate the eventual tool-result message
		# back to this call within the current loop iteration, never sent anywhere else.
		calls.append(
			ToolCallRequest(
				id=getattr(raw_call, "id", None) or str(uuid4()),
				name=function.name,
				arguments=dict(function.arguments or {}),
			)
		)
	return tuple(calls)


class OllamaLLMProvider(LLMProvider):
	"""The concrete LLMProvider, against any Ollama-compatible endpoint -- including Ollama
	Cloud. Mirrors OllamaEmbeddingProvider's own shape exactly: the client always talks to the
	local daemon at settings.ollama_host; Ollama itself routes a `:cloud`-suffixed model tag to
	its hosted infrastructure transparently, so nothing here needs to know which one is actually
	serving CHAT_MODEL_TAG.
	"""

	def __init__(
		self,
		*,
		host: str,
		api_key: str | None = None,
		model_tag: str = CHAT_MODEL_TAG,
		max_attempts: int = 3,
		base_retry_delay_seconds: float = 1.0,
	) -> None:
		self._host = host
		self._model_tag = model_tag
		self._max_attempts = max_attempts
		self._base_retry_delay_seconds = base_retry_delay_seconds
		self._client = AsyncClient(
			host=host, headers={"Authorization": f"Bearer {api_key}"} if api_key else None,
		)

	@classmethod
	def from_settings(cls) -> OllamaLLMProvider:
		settings = get_settings()
		return cls(host=settings.ollama_host, api_key=settings.ollama_api_key)

	@property
	def model_name(self) -> str:
		return self._model_tag

	async def stream_chat(
		self, *, messages: Sequence[ChatMessage], tools: Sequence[ToolSchema],
	) -> AsyncIterator[ChatDelta]:
		payload_messages = [_to_ollama_message(message) for message in messages]
		payload_tools = [_to_ollama_tool(tool) for tool in tools]

		stream = await self._open_stream(payload_messages, payload_tools)
		async for chunk in stream:
			message = chunk.message
			done = bool(getattr(chunk, "done", False))
			# Tool calls arrive as a completed structured field on the final chunk, never
			# incrementally the way prose content does.
			tool_calls = _from_ollama_tool_calls(getattr(message, "tool_calls", None)) if done else ()
			yield ChatDelta(content=message.content or "", done=done, tool_calls=tool_calls)

	async def _open_stream(self, messages: list[dict], tools: list[dict]):
		"""Retry/backoff covers establishing the stream (the first chunk) only. A failure partway
		through an already-started stream propagates as-is rather than silently retrying -- by
		then some content may already have been forwarded over SSE, and re-issuing the call would
		duplicate it."""
		last_error: Exception | None = None
		for attempt in range(1, self._max_attempts + 1):
			try:
				return await self._client.chat(
					model=self._model_tag, messages=messages, tools=tools or None, stream=True,
				)
			except Exception as exc:  # noqa: BLE001 -- the ollama client raises several unrelated types
				last_error = exc
				if attempt < self._max_attempts:
					await asyncio.sleep(self._base_retry_delay_seconds * 2 ** (attempt - 1))

		raise LLMProviderUnavailable(
			f"Ollama at {self._host} failed to open a chat stream with {self._model_tag!r} after "
			f"{self._max_attempts} attempts: {last_error}"
		) from last_error
