from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from app.modules.knowledge_base.application.commands.rebuild_similarity_graph.command import (
	RebuildSimilarityGraphCommand,
)
from app.modules.knowledge_base.application.commands.rebuild_similarity_graph.handler import (
	RebuildSimilarityGraphHandler,
)
from app.modules.knowledge_base.application.interfaces.recalculation_runner import RecalculationRunner
from app.modules.knowledge_base.application.services.similarity_computation import SimilarityComputation
from app.modules.knowledge_base.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.knowledge_base.infrastructure.vector_store.client import get_qdrant_client
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_similarity_search import QdrantSimilaritySearch

logger = logging.getLogger(__name__)


class SimilarityRecalculationRunner(RecalculationRunner):
	"""Composes and runs one full recalculation, and lets only one run at a time.

	Everything about *what* a pass does lives in RebuildSimilarityGraphHandler, which is also what
	the maintenance CLI drives. This class exists for the two things that are specific to running
	it as background work: assembling its collaborators outside of any request, and being the one
	object both entry points share so "one at a time" is a property of the operation rather than a
	rule each caller remembers.

	Collaborators are built per run rather than held. They are stateless wrappers over the pooled
	Qdrant client, so building them costs nothing, and doing it inside `run` rather than in
	`__init__` is what lets this be a module-level singleton without the import of this module
	depending on a reachable vector store -- `get_qdrant_client` raises when the endpoint is unset,
	and at import time there would be nobody to report that to.

	Failures are not caught here. A pass raises like any other handler, and `run_job` -- which
	wraps both the scheduled firing and the enqueued manual one -- logs it against the job name and
	stops there. That is deliberate rather than lenient: a failed rebuild leaves the previous
	graph exactly as it was, which is stale but coherent, and the next run repairs it. There is no
	retry, because a retry of a pass that failed on an unreachable Qdrant or a mixed-model corpus
	fails again for the same reason, and the schedule already provides the retry that matters.
	"""

	def __init__(self) -> None:
		self._running = False

	@property
	def is_running(self) -> bool:
		return self._running

	async def run(self) -> None:
		if self._running:
			# Reached when a schedule fires while a manual run is in flight, or the reverse. The
			# flag is set and cleared without an await in between, so on a single event loop this
			# check and the assignment below cannot be interleaved -- no lock is needed to make it
			# exclusive, and one would only obscure that.
			logger.info("Full similarity graph recalculation skipped: a pass is already running.")
			return

		self._running = True
		started = time.monotonic()
		logger.info("Full similarity graph recalculation started.")
		try:
			qdrant = get_qdrant_client()
			handler = RebuildSimilarityGraphHandler(
				uow_factory=SqlAlchemyUnitOfWork,
				knowledge_items=QdrantKnowledgeItemRepository(qdrant),
				computation=SimilarityComputation(QdrantSimilaritySearch(qdrant)),
			)
			# `generated_at` is the moment the pass began, not each row's write time, so every edge
			# written by one run carries the same stamp and a run reads back as one act.
			report = await handler.handle(RebuildSimilarityGraphCommand(generated_at=datetime.now(UTC)))
			logger.info(
				"Full similarity graph recalculation completed in %.1fs: %d items processed, "
				"%d results written, %d sources with no match above the threshold.",
				time.monotonic() - started, report.items_processed, report.results_written,
				report.sources_without_results,
			)
		finally:
			# In a finally so that a failure -- or a cancellation at shutdown -- does not leave the
			# process believing a pass is running forever, which would refuse every manual trigger
			# and skip every scheduled firing until a restart.
			self._running = False


# One per process, mirroring `job_queue` and `storage_service`: the in-flight flag is process-wide
# state, and a second instance would be a second flag that knows nothing about the first -- which
# is precisely the situation the flag exists to prevent.
similarity_recalculation_runner: RecalculationRunner = SimilarityRecalculationRunner()
