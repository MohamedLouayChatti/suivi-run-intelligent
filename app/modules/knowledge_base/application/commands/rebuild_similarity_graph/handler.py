from __future__ import annotations

import logging
from collections.abc import Callable
from uuid import UUID

from app.modules.knowledge_base.application.commands.rebuild_similarity_graph.command import (
	RebuildSimilarityGraphCommand,
)
from app.modules.knowledge_base.application.dto.rebuild_report_dto import RebuildReportDTO
from app.modules.knowledge_base.application.exceptions import MixedEmbeddingCorpus
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.application.services.similarity_computation import SimilarityComputation
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository

logger = logging.getLogger(__name__)


class RebuildSimilarityGraphHandler:
	"""Recomputes every source ticket's results from the vectors already stored.

	Embeds nothing, which is what separates this from a backfill: the similarity graph is derived
	data over the corpus plus the current retrieval policy, so a threshold change, a ranking change
	or simply "enough tickets have accumulated that old results are stale" all invalidate the graph
	while leaving every vector perfectly valid. Re-deriving it is indexed queries, not model calls.

	Runs over the whole corpus rather than only tickets missing results, because that is the point:
	an existing row is exactly what a rebuild exists to replace. Each source's results are swapped
	wholesale via `replace_for_source`, so an interrupted run leaves a graph that is partly rebuilt
	and partly previous-generation but never partly-written for any single source.

	Publishes no SimilarityResultsGenerated. That event announces a business fact -- a newly created
	ticket now has similar incidents to look at -- and a bulk maintenance sweep is not that fact
	repeated once per historical ticket; emitting it here would tell every future subscriber that
	800 tickets were just created.

	Reads the corpus from one store and writes the graph to another, so a page is computed in full
	before any transaction is opened. Searching from inside an open transaction would hold it across
	a batch's worth of network round trips to the vector store for no benefit -- the graph write is
	the only thing that needs to be transactional, and it needs to be transactional only per batch.

	The computation is a separate constructor dependency rather than something reached through the
	UnitOfWork: the searches behind it are reads, and reads in this codebase stay structurally
	decoupled from any UoW even when, as here, they happen mid-write.
	"""

	def __init__(
		self,
		uow_factory: Callable[[], UnitOfWork],
		knowledge_items: KnowledgeItemRepository,
		computation: SimilarityComputation,
	) -> None:
		self.uow_factory = uow_factory
		self.knowledge_items = knowledge_items
		self.computation = computation

	async def handle(self, command: RebuildSimilarityGraphCommand) -> RebuildReportDTO:
		await self._assert_single_model_corpus()

		items_processed = results_written = sources_without_results = 0
		cursor: UUID | None = None

		while True:
			page, cursor = await self.knowledge_items.list_page(cursor=cursor, limit=command.batch_size)

			if page:
				# One asymmetry with the live per-ticket path is deliberate and shows up here rather
				# than in the shared computation: a rebuild searches the entire corpus, including
				# tickets created after the one being recomputed, while ingestion could only ever see
				# what already existed. That is correct for a rebuild -- it re-derives what the
				# current corpus implies rather than replaying history -- and it is why a rebuild
				# strictly improves older tickets' results.
				computed = [
					(item.source_id, await self.computation.results_for(item, command.generated_at))
					for item in page
				]
				async with self.uow_factory() as uow:
					for source_id, results in computed:
						await uow.similarity_results.replace_for_source(source_id, results)
					await uow.commit()

				items_processed += len(computed)
				results_written += sum(len(results) for _, results in computed)
				sources_without_results += sum(1 for _, results in computed if not results)

				logger.info(
					"Rebuild progress: %d items processed, %d results written, %d sources with no match",
					items_processed, results_written, sources_without_results,
				)

			# The store's own cursor decides when the traversal is done -- an empty page does not,
			# since a store is free to return one mid-traversal.
			if cursor is None:
				break

		return RebuildReportDTO(
			items_processed=items_processed, results_written=results_written,
			sources_without_results=sources_without_results,
		)

	async def _assert_single_model_corpus(self) -> None:
		present = await self.knowledge_items.distinct_model_versions()
		if len(present) > 1:
			raise MixedEmbeddingCorpus(present)
