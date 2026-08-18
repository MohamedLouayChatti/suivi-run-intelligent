from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from qdrant_client import AsyncQdrantClient, models

from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import (
	KnowledgeItemPage,
	KnowledgeItemRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store import collection, payload


class QdrantKnowledgeItemRepository(KnowledgeItemRepository):
	"""The corpus, in Qdrant.

	Every method here writes or reads immediately -- there is no session to stage into and no
	commit to wait for. That is why this repository is a dependency of its own rather than a member
	of the UnitOfWork, and why the handler that writes both an item and its similarity results
	writes the item first: the item is the durable half, and a failure after it lands leaves a
	ticket that is searchable but has no results row yet, which a rebuild repairs and which is in
	any case indistinguishable from a ticket with no match above the threshold.
	"""

	def __init__(self, client: AsyncQdrantClient) -> None:
		self.client = client

	async def add(self, item: KnowledgeItem) -> None:
		await self.add_many([item])

	async def add_many(self, items: Sequence[KnowledgeItem]) -> None:
		if not items:
			return
		await self.client.upsert(
			collection_name=collection.COLLECTION_NAME,
			points=[payload.knowledge_item_to_point(item) for item in items],
			# The caller is a batch loop that must not run ahead of what is actually stored: the
			# next batch's "which of these are already embedded?" question would otherwise race the
			# indexing of the batch before it and re-embed work already done.
			wait=True,
		)

	async def exists(self, source_id: UUID) -> bool:
		return bool(await self.existing_source_ids([source_id]))

	async def existing_source_ids(self, source_ids: Sequence[UUID]) -> set[UUID]:
		if not source_ids:
			return set()
		records, _ = await self.client.scroll(
			collection_name=collection.COLLECTION_NAME,
			scroll_filter=models.Filter(
				must=[
					models.FieldCondition(
						key=collection.SOURCE_ID,
						match=models.MatchAny(any=[str(source_id) for source_id in source_ids]),
					)
				]
			),
			# The answer is a set of ids; pulling 1024 floats per point to compute it would make a
			# resumability check the most expensive query in the pass.
			with_payload=[collection.SOURCE_ID],
			with_vectors=False,
			limit=len(source_ids),
		)
		return {UUID(record.payload[collection.SOURCE_ID]) for record in records if record.payload}

	async def get_by_source_ids(self, source_ids: Sequence[UUID]) -> list[KnowledgeItem]:
		if not source_ids:
			return []
		records, _ = await self.client.scroll(
			collection_name=collection.COLLECTION_NAME,
			scroll_filter=models.Filter(
				must=[
					models.FieldCondition(
						key=collection.SOURCE_ID,
						match=models.MatchAny(any=[str(source_id) for source_id in source_ids]),
					)
				]
			),
			with_payload=True,
			# The one difference from existing_source_ids next door, and the reason both exist: these
			# items are about to be searched *from*, so the vectors are the whole point rather than an
			# expensive way to answer a question about ids.
			with_vectors=True,
			limit=len(source_ids),
		)
		return [payload.point_to_knowledge_item(record) for record in records]

	async def list_page(self, *, cursor: UUID | None, limit: int) -> KnowledgeItemPage:
		records, next_offset = await self.client.scroll(
			collection_name=collection.COLLECTION_NAME,
			offset=str(cursor) if cursor is not None else None,
			limit=limit,
			with_payload=True,
			# The one read in this module that genuinely needs the vectors back: a rebuild re-runs
			# the searches from stored embeddings precisely so it never has to embed again.
			with_vectors=True,
		)
		items = [payload.point_to_knowledge_item(record) for record in records]
		return items, UUID(str(next_offset)) if next_offset is not None else None

	async def distinct_model_versions(self) -> list[tuple[str, str]]:
		"""Faceted on the version rather than scanned, then one tiny lookup per distinct version to
		recover the model name that produced it.

		`exact=True` is not optional here. Facet counts are approximate by default, and the thing
		this check exists to catch is precisely a rare value -- a few points left behind by an
		abandoned model swap -- which an approximate pass is entitled to miss. Missing it is the one
		outcome that cannot be detected later.

		In practice the loop below runs once: a healthy corpus has exactly one model build in it.
		"""
		facet = await self.client.facet(
			collection_name=collection.COLLECTION_NAME,
			key=collection.EMBEDDING_MODEL_VERSION,
			exact=True,
		)

		pairs = []
		for hit in facet.hits:
			version = str(hit.value)
			records, _ = await self.client.scroll(
				collection_name=collection.COLLECTION_NAME,
				scroll_filter=models.Filter(
					must=[
						models.FieldCondition(
							key=collection.EMBEDDING_MODEL_VERSION, match=models.MatchValue(value=version)
						)
					]
				),
				with_payload=[collection.EMBEDDING_MODEL],
				with_vectors=False,
				limit=1,
			)
			for record in records:
				if record.payload:
					pairs.append((record.payload[collection.EMBEDDING_MODEL], version))
		return pairs

	async def delete_all(self) -> None:
		# Points are removed but the collection and its payload indexes stay: this is "drop the
		# corpus", not "drop the schema", and re-provisioning after every reset would be an extra
		# step for a caller that only wanted the data gone. A condition-free filter selects
		# everything.
		await self.client.delete(
			collection_name=collection.COLLECTION_NAME,
			points_selector=models.FilterSelector(filter=models.Filter()),
			wait=True,
		)
