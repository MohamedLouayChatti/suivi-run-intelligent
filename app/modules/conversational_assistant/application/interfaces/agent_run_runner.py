from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID


class AgentRunRunner(ABC):
	"""Runs one agent turn for an already-persisted Run.

	Implemented by a process-wide Infrastructure singleton (mirrors Knowledge Base's
	RecalculationRunner/SimilarityRecalculationRunner split): the Application-layer command
	handler that starts a turn depends on this port and knows nothing about LangGraph, the LLM
	provider, or how tool authorization is wired -- all of that is Infrastructure's concern.
	"""

	@abstractmethod
	async def run(self, *, conversation_id: UUID, run_id: UUID) -> None:
		raise NotImplementedError
