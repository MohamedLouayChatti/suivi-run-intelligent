from __future__ import annotations

from app.shared.ai.embedding_provider import EmbeddingProvider


class UnimplementedEmbeddingProvider(EmbeddingProvider):
	"""Wired in so the module is importable and startable end-to-end before an embedding model
	is chosen (see knowledge_base/CLAUDE.md §11). Safe to leave wired: InMemoryEventBus.publish
	catches and logs handler exceptions without aborting the rest of ticket creation, so a real
	TicketCreated will still succeed -- only the similarity pipeline itself will log and no-op
	until this is replaced with a real Ollama Cloud implementation.
	"""

	@property
	def model_name(self) -> str:
		raise NotImplementedError("No embedding model has been chosen yet -- see knowledge_base/CLAUDE.md §11.")

	@property
	def model_version(self) -> str:
		raise NotImplementedError("No embedding model has been chosen yet -- see knowledge_base/CLAUDE.md §11.")

	async def embed(self, text: str) -> list[float]:
		raise NotImplementedError("No embedding provider has been implemented yet -- see knowledge_base/CLAUDE.md §11.")
