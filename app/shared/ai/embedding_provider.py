from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
	"""Port for turning text into a vector embedding. Application code only ever depends on this
	abstraction -- never a specific provider (Ollama Cloud or otherwise) directly. Only
	Infrastructure implements it.

	model_name/model_version are exposed so callers can stamp generated embeddings with the
	model that produced them without needing to know which concrete provider is behind this port.
	"""

	@property
	@abstractmethod
	def model_name(self) -> str:
		raise NotImplementedError

	@property
	@abstractmethod
	def model_version(self) -> str:
		raise NotImplementedError

	async def warm_up(self) -> None:
		"""Resolve and validate whatever provider-side state the first embed() would otherwise
		resolve lazily -- model availability, the exact build identity behind model_version.

		Defaults to a no-op, so a provider with nothing to resolve implements nothing. Two kinds
		of caller need it: anything reading model_name/model_version *before* producing an
		embedding, and any long batch run that would rather fail in the first second than in the
		twentieth minute. Implementations must be idempotent and safe to call concurrently.
		"""
		return None

	@abstractmethod
	async def embed(self, text: str) -> list[float]:
		raise NotImplementedError
