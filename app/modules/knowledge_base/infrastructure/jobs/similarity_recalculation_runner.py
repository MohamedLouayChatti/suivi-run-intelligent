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
from app.modules.knowledge_base.domain.enums.recalculation_trigger import RecalculationTrigger
from app.modules.knowledge_base.domain.events.similarity_graph_recalculated import SimilarityGraphRecalculated
from app.modules.knowledge_base.domain.events.similarity_graph_recalculation_failed import (
	SimilarityGraphRecalculationFailed,
)
from app.modules.knowledge_base.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.knowledge_base.infrastructure.vector_store.client import get_qdrant_client
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_similarity_search import QdrantSimilaritySearch
from app.shared.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class SimilarityRecalculationRunner(RecalculationRunner):
	"""Composes and runs one full recalculation, lets only one run at a time, and says how it went.

	Everything about *what* a pass does lives in RebuildSimilarityGraphHandler, which is also what
	the maintenance CLI drives. This class exists for the three things that are specific to running
	it as background work: assembling its collaborators outside of any request, being the one
	object every entry point shares so "one at a time" is a property of the operation rather than a
	rule each caller remembers, and announcing the outcome to a system that has no response to read
	it from.

	Collaborators are built per run rather than held. They are stateless wrappers over the pooled
	Qdrant client, so building them costs nothing, and doing it inside `run` rather than in
	`__init__` is what lets this be a module-level singleton without the import of this module
	depending on a reachable vector store -- `get_qdrant_client` raises when the endpoint is unset,
	and at import time there would be nobody to report that to.

	Failures are announced and re-raised, never swallowed. The pass still raises, `run_job` still
	logs it against the job name, there is still no retry, and the schedule is still the retry that
	matters -- a failed rebuild leaves the previous graph exactly as it was, which is stale but
	coherent, and the next run repairs it. What publishing adds is that "stale but coherent" stops
	being a state only a log line knows about: the audit log records it and the administrators are
	told, which is the difference between a graph everyone knows is stale and one that quietly is.
	"""

	def __init__(self) -> None:
		self._running = False
		self._event_publisher: EventPublisher | None = None

	def bind_event_publisher(self, event_publisher: EventPublisher) -> None:
		"""Give this runner the publisher it announces outcomes through.

		Bound at startup rather than injected at construction because this is a process-wide
		singleton created at import time, when no event bus exists yet -- the bus is built by the
		lifespan, which is also where every module's subscriptions are registered, so that is the
		moment this can be handed one.

		Until it is bound, a pass runs and publishes nothing. That is the honest behaviour rather
		than a failure: the only entry points that reach this object live in the API process, where
		binding always happens, and the CLI drives RebuildSimilarityGraphHandler directly without
		passing through here at all.
		"""
		self._event_publisher = event_publisher

	@property
	def is_running(self) -> bool:
		return self._running

	async def run(self, trigger: RecalculationTrigger) -> None:
		if self._running:
			# Reached when a schedule fires while a manual run is in flight, or the reverse. The
			# flag is set and cleared without an await in between, so on a single event loop this
			# check and the assignment below cannot be interleaved -- no lock is needed to make it
			# exclusive, and one would only obscure that.
			#
			# Nothing is published for a skip. No pass ran, so there is no outcome to record, and
			# an event here would put a row in the audit log for something that did not happen.
			logger.info("Full similarity graph recalculation skipped: a pass is already running.")
			return

		self._running = True
		started = time.monotonic()
		logger.info("Full similarity graph recalculation started (%s).", trigger.value)
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
		except Exception as error:
			duration = time.monotonic() - started
			logger.exception("Full similarity graph recalculation failed after %.1fs.", duration)
			# Announced before the re-raise, and deliberately not inside the finally below: a
			# cancellation at shutdown must reach that finally without being reported as a failed
			# pass, since nothing went wrong -- the process was asked to stop.
			await self._publish(
				SimilarityGraphRecalculationFailed(
					trigger=trigger,
					reason=str(error) or type(error).__name__,
					duration_seconds=duration,
					occurred_at=datetime.now(UTC),
				)
			)
			raise
		else:
			duration = time.monotonic() - started
			logger.info(
				"Full similarity graph recalculation completed in %.1fs: %d items processed, "
				"%d results written, %d sources with no match above the threshold.",
				duration, report.items_processed, report.results_written, report.sources_without_results,
			)
			await self._publish(
				SimilarityGraphRecalculated(
					trigger=trigger,
					items_processed=report.items_processed,
					results_written=report.results_written,
					sources_without_results=report.sources_without_results,
					duration_seconds=duration,
					occurred_at=datetime.now(UTC),
				)
			)
		finally:
			# In a finally so that a failure -- or a cancellation at shutdown -- does not leave the
			# process believing a pass is running forever, which would refuse every manual trigger
			# and skip every scheduled firing until a restart.
			self._running = False

	async def _publish(self, event: SimilarityGraphRecalculated | SimilarityGraphRecalculationFailed) -> None:
		"""Announce an outcome, if there is anywhere to announce it to.

		The bus logs a failing subscriber and carries on, so a publish cannot turn a successful
		pass into a failed one. What it could still do is raise on its own account, which would
		replace a real recalculation failure with an unrelated one on the way out of the except
		block above -- so this stays a plain call over a guard, with no error handling of its own
		to be wrong about.
		"""
		if self._event_publisher is None:
			return
		await self._event_publisher.publish(event)


# One per process, mirroring `job_queue` and `storage_service`: the in-flight flag is process-wide
# state, and a second instance would be a second flag that knows nothing about the first -- which
# is precisely the situation the flag exists to prevent. Typed as the concrete class rather than
# the port because startup binds a publisher onto it, which is composition rather than running and
# so has no place on the port every caller depends on.
similarity_recalculation_runner = SimilarityRecalculationRunner()
