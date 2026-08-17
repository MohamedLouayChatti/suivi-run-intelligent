from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

from app.modules.knowledge_base.application.commands.rebuild_similarity_graph.command import (
	RebuildSimilarityGraphCommand,
)
from app.modules.knowledge_base.application.dto.rebuild_report_dto import RebuildReportDTO
from app.modules.knowledge_base.application.exceptions import MixedEmbeddingCorpus
from app.modules.knowledge_base.application.interfaces.similarity_search_port import SimilaritySearchPort
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.domain.services.similarity_ranking import (
	ALGORITHM_VERSION,
	MAX_RESULTS,
	MIN_SIMILARITY_THRESHOLD,
	rank_candidates,
)

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

	The search port is a separate constructor dependency rather than something reached through the
	UnitOfWork: it is a read, and reads in this codebase stay structurally decoupled from any UoW
	even when, as here, they happen mid-write.
	"""

	def __init__(
		self,
		uow_factory: Callable[[], UnitOfWork],
		search_port: SimilaritySearchPort,
	) -> None:
		self.uow_factory = uow_factory
		self.search_port = search_port

	async def handle(self, command: RebuildSimilarityGraphCommand) -> RebuildReportDTO:
		await self._assert_single_model_corpus()

		items_processed = results_written = sources_without_results = 0
		after_id: UUID | None = None

		while True:
			async with self.uow_factory() as uow:
				page = await uow.knowledge_items.list_page(after_id=after_id, limit=command.batch_size)
				if not page:
					break
				after_id = page[-1].id

				for item in page:
					results = await self._results_for(item, command.generated_at)
					await uow.similarity_results.replace_for_source(item.source_id, results)
					items_processed += 1
					results_written += len(results)
					if not results:
						sources_without_results += 1

				await uow.commit()

			logger.info(
				"Rebuild progress: %d items processed, %d results written, %d sources with no match",
				items_processed, results_written, sources_without_results,
			)

		return RebuildReportDTO(
			items_processed=items_processed, results_written=results_written,
			sources_without_results=sources_without_results,
		)

	async def _results_for(self, item: KnowledgeItem, generated_at: datetime) -> list[SimilarityResult]:
		"""The same two searches and the same ranking policy the live per-ticket path runs -- called
		here, not restated, so the graph a rebuild produces cannot drift from the one ingestion
		produces.

		One asymmetry with the live path is deliberate: a rebuild searches the entire corpus,
		including tickets created after this one, while ingestion could only ever see what already
		existed. That is correct for a rebuild -- it is recomputing what the current corpus implies,
		not replaying history -- and it is why a rebuild strictly improves older tickets' results.

		`embedding_model_version` is copied from the item rather than from a provider: the vector
		being ranked was produced by that model, and this pass has no provider to ask.
		"""
		semantic = await self.search_port.find_nearest(
			item.embedding, application=item.application,
			exclude_ticket_id=item.source_id, limit=MAX_RESULTS,
		)
		referenced = await self.search_port.find_referenced(
			item.embedding, item.identifiers,
			application=item.application, exclude_ticket_id=item.source_id,
		)
		ranked = rank_candidates(
			semantic=semantic, referenced=referenced,
			min_similarity_score=MIN_SIMILARITY_THRESHOLD, max_results=MAX_RESULTS,
		)
		return [
			SimilarityResult.create(
				id=uuid4(), source_ticket_id=item.source_id, similar_ticket_id=candidate.ticket_id,
				similarity_score=candidate.similarity_score, rank=candidate.rank,
				generated_at=generated_at, embedding_model_version=item.embedding_model_version,
				algorithm_version=ALGORITHM_VERSION,
			)
			for candidate in ranked
		]

	async def _assert_single_model_corpus(self) -> None:
		async with self.uow_factory() as uow:
			present = await uow.knowledge_items.distinct_model_versions()
		if len(present) > 1:
			raise MixedEmbeddingCorpus(present)
