from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem


class KnowledgeItemRepository(ABC):
	@abstractmethod
	async def add(self, item: KnowledgeItem) -> None:
		raise NotImplementedError

	@abstractmethod
	async def exists(self, source_id: UUID) -> bool:
		raise NotImplementedError

	@abstractmethod
	async def existing_source_ids(self, source_ids: Sequence[UUID]) -> set[UUID]:
		"""The subset of `source_ids` already embedded. The batch form of `exists`, and what makes
		a bulk backfill resumable: it can be re-run over the whole corpus at any time and will only
		do the work still missing, instead of asking one question per candidate."""
		raise NotImplementedError

	@abstractmethod
	async def list_page(self, *, after_id: UUID | None, limit: int) -> list[KnowledgeItem]:
		"""One page of items, ordered by id, for a full pass over the corpus.

		Keyset rather than LIMIT/OFFSET, for the same reason the ticket-side pass is: rows may be
		inserted underneath a long traversal, and OFFSET would then skip or repeat items.
		"""
		raise NotImplementedError

	@abstractmethod
	async def distinct_model_versions(self) -> list[tuple[str, str]]:
		"""Every (embedding_model, embedding_model_version) pair present in the corpus.

		Exists to make one specific corruption detectable before it happens: vectors from two
		different models share no comparable coordinate space, so a similarity graph built across
		a mixed corpus is meaningless while still looking perfectly well-formed. More than one pair
		here means re-embed before rebuilding.
		"""
		raise NotImplementedError

	@abstractmethod
	async def delete_all(self) -> None:
		"""Drop the whole corpus, for a model change. Safe to expose because knowledge items are
		derived data -- they are recomputable in full from the tickets they were built from."""
		raise NotImplementedError
