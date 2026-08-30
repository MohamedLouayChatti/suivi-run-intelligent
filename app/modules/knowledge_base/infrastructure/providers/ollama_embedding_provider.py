from __future__ import annotations

import asyncio
import logging

from ollama import AsyncClient

from app.modules.knowledge_base.infrastructure.embedding_model import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL_TAG
from app.shared.ai.embedding_provider import EmbeddingProvider
from app.shared.config.settings import get_settings

logger = logging.getLogger(__name__)

# Ollama reports full 64-character digests; the column is String(50) and a prefix already
# distinguishes one build of a model from another. 19 matches the digests recorded by the
# evaluation notebook's model_info.json, so a stamped row can be read straight back against it.
_DIGEST_LENGTH = 19

# How long Ollama keeps the weights resident after an embed, overriding its 5-minute default.
#
# This is a memory-for-latency trade, and the numbers it is set against are this deployment's: the
# model is ~1.2 GB on a CPU-only 16 GB machine, and the team creates on the order of eight tickets
# a day. Under the default those eight arrive far enough apart that nearly every one pays a full
# cold load from disk; two hours is long enough that a working day's tickets cluster onto one load,
# and short enough that an idle evening gives the memory back rather than holding it overnight.
#
# Not a setting, for the same reason the retry policy is not: it describes how this module wants to
# use an Ollama, not where that Ollama is. It is also only a hint -- a remote or cloud endpoint is
# free to manage residency however it likes, and nothing here depends on it being honoured.
_MODEL_KEEP_ALIVE = "2h"


class EmbeddingProviderUnavailable(RuntimeError):
	"""Ollama could not be reached, or does not have the pinned model."""


class EmbeddingModelMismatch(RuntimeError):
	"""The model Ollama is serving under the pinned tag is not the one this module is built for."""


class EmbeddingProviderNotWarmedUp(RuntimeError):
	"""model_version was read before any embedding was produced and before warm_up() ran."""


class OllamaEmbeddingProvider(EmbeddingProvider):
	"""The concrete EmbeddingProvider, against any Ollama-compatible endpoint.

	One implementation covers a local daemon, a remote GPU machine on the LAN and Ollama Cloud,
	because the only thing that differs between them is the host (and, for the cloud, a bearer
	token). That is why the host is configuration and the model is not: moving where inference
	runs must never be able to change *which* model produced a stored vector.

	`model_version` is the model's Ollama digest rather than its tag: a tag is mutable, so
	re-pulling `bge-m3` can change the weights behind an unchanged name. Stamping the digest is
	what turns a model upgrade into a detectable "these rows came from a different build" instead
	of a silent quality regression -- the traceability the module's reproducibility rule asks for.
	Resolving it costs an HTTP round trip, so it happens lazily on first use rather than at
	construction: this class is built during application startup, which must not do network I/O
	and must not fail to boot because Ollama is down.
	"""

	def __init__(
		self,
		*,
		host: str,
		api_key: str | None = None,
		model_tag: str = EMBEDDING_MODEL_TAG,
		max_attempts: int = 3,
		base_retry_delay_seconds: float = 1.0,
		keep_alive: str = _MODEL_KEEP_ALIVE,
	) -> None:
		self._host = host
		self._model_tag = model_tag
		self._max_attempts = max_attempts
		self._base_retry_delay_seconds = base_retry_delay_seconds
		self._keep_alive = keep_alive
		self._client = AsyncClient(
			host=host, headers={"Authorization": f"Bearer {api_key}"} if api_key else None
		)
		self._model_version: str | None = None
		self._warm_up_lock = asyncio.Lock()

	@classmethod
	def from_settings(cls) -> OllamaEmbeddingProvider:
		settings = get_settings()
		return cls(host=settings.ollama_host, api_key=settings.ollama_api_key)

	@property
	def model_name(self) -> str:
		return self._model_tag

	@property
	def model_version(self) -> str:
		if self._model_version is None:
			raise EmbeddingProviderNotWarmedUp(
				"model_version is only known once the model has been resolved -- await embed() or "
				"warm_up() first."
			)
		return self._model_version

	async def warm_up(self) -> None:
		"""Resolve the served model's digest and check it is the build this module expects.

		Double-checked under a lock because a single provider instance is shared across concurrent
		requests: without it, N simultaneous first-embeds would each issue their own resolution.
		"""
		if self._model_version is not None:
			return
		async with self._warm_up_lock:
			if self._model_version is not None:
				return
			self._model_version = await self._resolve_model_version()
			logger.info(
				"Embedding provider ready: model=%s digest=%s host=%s",
				self._model_tag, self._model_version, self._host,
			)

	async def embed(self, text: str) -> list[float]:
		await self.warm_up()

		last_error: Exception | None = None
		for attempt in range(1, self._max_attempts + 1):
			try:
				response = await self._client.embed(
					model=self._model_tag, input=text, keep_alive=self._keep_alive
				)
				return list(response.embeddings[0])
			except Exception as exc:  # noqa: BLE001 -- the ollama client raises several unrelated types
				last_error = exc
				if attempt < self._max_attempts:
					await asyncio.sleep(self._base_retry_delay_seconds * 2 ** (attempt - 1))

		raise EmbeddingProviderUnavailable(
			f"Ollama at {self._host} failed to embed with {self._model_tag!r} after "
			f"{self._max_attempts} attempts: {last_error}"
		) from last_error

	async def _resolve_model_version(self) -> str:
		try:
			shown = await self._client.show(self._model_tag)
			listed = await self._client.list()
		except Exception as exc:  # noqa: BLE001 -- connection, HTTP and response errors alike
			raise EmbeddingProviderUnavailable(
				f"Ollama at {self._host} could not describe model {self._model_tag!r}: {exc}. "
				f"Check OLLAMA_HOST, that the daemon is reachable from this machine (a remote one "
				f"must be started with OLLAMA_HOST=0.0.0.0, not the loopback default), and that "
				f"the model is pulled there (`ollama pull {self._model_tag}`)."
			) from exc

		self._assert_expected_dimensions(shown)

		entry = next((model for model in listed.models if model.model == self._full_tag()), None)
		if entry is None or not entry.digest:
			raise EmbeddingProviderUnavailable(
				f"Ollama at {self._host} reports no digest for {self._model_tag!r}, so the exact "
				f"model build cannot be recorded alongside the embeddings it produces."
			)
		return entry.digest[:_DIGEST_LENGTH]

	def _assert_expected_dimensions(self, shown: object) -> None:
		"""Catches the failure that would otherwise surface as a Postgres error 800 rows in, or --
		worse -- as a silently mis-calibrated similarity threshold if a same-dimension model were
		swapped in behind the tag.
		"""
		model_info = getattr(shown, "modelinfo", None) or {}
		dimensions = next(
			(value for key, value in model_info.items() if key.endswith("embedding_length")), None
		)
		if dimensions is None:
			logger.warning(
				"Ollama did not report an embedding length for %s; skipping the dimension check.",
				self._model_tag,
			)
			return
		if dimensions != EMBEDDING_DIMENSIONS:
			raise EmbeddingModelMismatch(
				f"{self._model_tag!r} on {self._host} produces {dimensions}-dimensional embeddings, "
				f"but this module is built for {EMBEDDING_DIMENSIONS} (the vector column's width and "
				f"the calibrated similarity threshold both assume it)."
			)

	def _full_tag(self) -> str:
		"""`list()` always reports a fully-qualified tag (`bge-m3` -> `bge-m3:latest`), so a lookup
		against its response has to normalize first or an untagged reference never matches."""
		return self._model_tag if ":" in self._model_tag else f"{self._model_tag}:latest"
