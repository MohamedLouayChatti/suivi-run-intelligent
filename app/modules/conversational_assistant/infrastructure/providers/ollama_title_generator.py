from __future__ import annotations

import asyncio

from ollama import AsyncClient

from app.modules.conversational_assistant.application.interfaces.conversation_title_generator import (
	ConversationTitleGenerator,
)
from app.modules.conversational_assistant.application.titling.prompt import (
	TITLE_INSTRUCTIONS,
	build_title_prompt,
)
from app.modules.conversational_assistant.infrastructure.providers.chat_model import TITLE_MODEL_TAG
from app.shared.config.settings import get_settings

# One attempt, and a bound on how long it may take. Both follow from what this call is for: a
# conversation already has a usable interim title, so a failure costs nothing a retry would buy
# back, and spending cloud tokens re-asking for a cosmetic label nobody is waiting on is not a
# trade worth making. This is the deliberate difference from OllamaLLMProvider, which retries three
# times with backoff because an agent turn failing means the user gets no answer at all.
_TIMEOUT_SECONDS = 15.0

# Low but not zero: a title is a summary, where the obvious phrasing is the right one, and a model
# free to be creative here produces a different name for the same question on every run.
_TEMPERATURE = 0.2


class TitleGeneratorUnavailable(RuntimeError):
	"""Ollama could not be reached, timed out, or returned nothing for a title."""


class OllamaTitleGenerator(ConversationTitleGenerator):
	"""The concrete ConversationTitleGenerator, against any Ollama-compatible endpoint.

	Mirrors OllamaLLMProvider's own shape: the client always talks to the daemon at
	settings.ollama_host, and Ollama routes a `:cloud`-suffixed tag to its hosted infrastructure
	transparently, so nothing here knows or cares which machine serves TITLE_MODEL_TAG. Host and
	credential are configuration; the model is not, for the reason settings.py states -- moving
	where inference runs must never be able to change which model produced a result.

	A separate AsyncClient instance from the agent's rather than a shared one: constructing it is
	local work (it builds an HTTP client, it does not connect), and sharing would tie the two
	models' transport settings together for no gain.
	"""

	def __init__(
		self,
		*,
		host: str,
		api_key: str | None = None,
		model_tag: str = TITLE_MODEL_TAG,
		timeout_seconds: float = _TIMEOUT_SECONDS,
	) -> None:
		self._host = host
		self._model_tag = model_tag
		self._timeout_seconds = timeout_seconds
		self._client = AsyncClient(
			host=host, headers={"Authorization": f"Bearer {api_key}"} if api_key else None,
		)

	@classmethod
	def from_settings(cls) -> OllamaTitleGenerator:
		settings = get_settings()
		return cls(host=settings.ollama_host, api_key=settings.ollama_api_key)

	@property
	def model_name(self) -> str:
		return self._model_tag

	async def generate(self, first_message: str) -> str:
		messages = [
			{"role": "system", "content": TITLE_INSTRUCTIONS},
			{"role": "user", "content": build_title_prompt(first_message)},
		]
		try:
			async with asyncio.timeout(self._timeout_seconds):
				response = await self._client.chat(
					model=self._model_tag,
					messages=messages,
					# No `tools` argument at all, rather than an empty list: this call must never be
					# answerable with a tool call. It is not part of the agent and has no loop to
					# execute one in.
					stream=False,
					options={"temperature": _TEMPERATURE},
				)
		except asyncio.CancelledError:
			# Shutdown, not a provider failure -- asyncio.timeout raises TimeoutError for its own
			# expiry, so a CancelledError arriving here came from outside and is re-raised so the
			# cancellation that asked for it takes effect.
			raise
		except Exception as exc:  # noqa: BLE001 -- the ollama client raises several unrelated types
			raise TitleGeneratorUnavailable(
				f"Ollama at {self._host} could not produce a title with {self._model_tag!r}: {exc}"
			) from exc

		content = (response.message.content or "").strip()
		if not content:
			raise TitleGeneratorUnavailable(
				f"Ollama at {self._host} returned an empty title with {self._model_tag!r}."
			)
		return content
