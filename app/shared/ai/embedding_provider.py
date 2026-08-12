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

	@abstractmethod
	async def embed(self, text: str) -> list[float]:
		raise NotImplementedError
