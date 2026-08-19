from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem

# One page of a full traversal, plus the cursor that resumes it. `None` means the traversal is
# finished -- distinct from an empty page, which a store is free to return mid-traversal.
KnowledgeItemPage = tuple[list[KnowledgeItem], UUID | None]


class KnowledgeItemRepository(ABC):
	"""The corpus. Unlike every other repository in this module it is not reached through the
	UnitOfWork: knowledge items live in a vector store with no transaction shared with Postgres, so
	presenting it behind a commit/rollback that cannot cover it would be a lie about what happens
	on failure. Callers take it as a dependency of its own and are written knowing each write lands
	immediately.

	Writes are upserts keyed by item id, which is what makes an interrupted pass safe to simply
	re-run.
	"""

	@abstractmethod
	async def add(self, item: KnowledgeItem) -> None:
		raise NotImplementedError

	@abstractmethod
	async def add_many(self, items: Sequence[KnowledgeItem]) -> None:
		"""A whole batch in one round trip. The bulk counterpart of `add`, and the reason a backfill
		costs one write per batch rather than one per ticket -- which matters now that a write is a
		network call rather than a row staged in an open session."""
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
	async def get_by_source_ids(self, source_ids: Sequence[UUID]) -> list[KnowledgeItem]:
		"""The full items -- vectors included -- behind a known set of source ids.

		The targeted counterpart of `list_page`: the neighbour refresh knows exactly whose results
		it is about to recompute and needs those tickets' own vectors to search from, where a full
		pass walks the whole corpus in the store's own order. Distinct from `existing_source_ids`,
		which answers a membership question and deliberately leaves the vectors on the server.

		Ids with no item are simply absent from the result rather than an error: the caller is
		asking about a corpus whose contents it does not control.
		"""
		raise NotImplementedError

	@abstractmethod
	async def list_page(self, *, cursor: UUID | None, limit: int) -> KnowledgeItemPage:
		"""One page of the corpus for a full pass, with the cursor to resume from.

		Cursor-based rather than offset-based, for the same reason the ticket-side pass is: items
		may be written underneath a long traversal, and an offset would then skip or repeat them.
		The cursor is the store's own -- passing back what it handed out is what makes complete
		traversal its guarantee rather than an assumption this module makes about its ordering.
		"""
		raise NotImplementedError

	@abstractmethod
	async def distinct_model_versions(self) -> list[tuple[str, str]]:
		"""Every (embedding_model, embedding_model_version) pair present in the corpus.

		Exists to make one specific corruption detectable before it happens: vectors from two
		different models share no comparable coordinate space, so a similarity graph built across
		a mixed corpus is meaningless while still looking perfectly well-formed. More than one pair
		here means re-embed before rebuilding.

		Must count exactly, not approximately. The value this is looking for is by nature a rare
		one -- a handful of stray points left by a half-finished model swap -- and an estimate is
		free to miss exactly that.
		"""
		raise NotImplementedError

	@abstractmethod
	async def delete_by_source_ids(self, source_ids: Sequence[UUID]) -> None:
		"""Remove the items for these sources, if they are there.

		The compensating half of `add_many`, and the only reason it exists: a batch import writes
		its tickets to one store and their vectors to another with no transaction across the two,
		so the only way it can promise all-or-nothing is to be able to take back what it wrote when
		the second write fails. Nothing else in this module deletes selectively -- the maintenance
		passes replace or drop everything.

		Silent about ids with no item, like `get_by_source_ids`: a caller undoing a partial write
		does not know how much of it landed, and having to find out first would be the same
		round trip twice.
		"""
		raise NotImplementedError

	@abstractmethod
	async def delete_all(self) -> None:
		"""Drop the whole corpus, for a model change. Safe to expose because knowledge items are
		derived data -- they are recomputable in full from the tickets they were built from."""
		raise NotImplementedError
