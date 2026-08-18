from __future__ import annotations

from app.modules.knowledge_base.application.commands.refresh_neighbor_similarity.command import (
	RefreshNeighborSimilarityCommand,
)
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.application.services.similarity_computation import SimilarityComputation
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository


class RefreshNeighborSimilarityHandler:
	"""Bounded incremental refresh: after `source -> [a, b]`, re-runs the search for `a` and `b` so
	the new ticket can enter *their* results too.

	Exists because similarity is directed. "B is a top match for A" does not make A a top match for
	B -- whether it is depends on what else B already matches -- so the reverse edge can never be
	synthesised from the forward one, only searched for. Without this pass a newly created ticket
	is reachable only from itself: every older ticket keeps the results it was born with until the
	next full rebuild, which is a graph that grows steadily more stale in one direction while
	looking perfectly healthy in the other.

	Exactly one hop, never recursive. Refreshing a neighbour can change that neighbour's results,
	which by the same argument could change *its* neighbours' -- and following that is an unbounded
	traversal of the graph inside a ticket-creation request. Converging the whole graph is the
	rebuild's job; this is the slice of it worth paying for inline, and the trade is deliberate:
	one hop costs a bounded handful of searches and leaves the rest of the graph exactly as stale
	as it already was, which is the state a rebuild exists to repair anyway.

	Embeds nothing, which is what makes it affordable at all: every neighbour's vector is already
	in the corpus, so the cost is vector searches and one graph write per neighbour rather than a
	model call per neighbour.

	Runs in its own transaction, separate from the one that wrote the source ticket's own results.
	Those are committed before this handler is ever invoked and must never be put at risk by it --
	they are the outcome a reader of the new ticket is waiting for, while this is maintenance on
	rows nobody is looking at yet.

	That same asymmetry is why the ticket-creation path enqueues this as a background job rather
	than awaiting it: nothing in the request reads what it writes. Nothing here assumes it, though.
	The handler takes a ticket id and reads everything else from committed state, so it computes the
	same thing whether it runs immediately, seconds later on a background runner, or from an
	operator's trigger -- which is what makes it deferrable in the first place rather than merely
	deferred.

	What a failure means is the caller's decision, not this handler's, so it raises normally: on the
	background runner `run_job` logs it and stops there, since the neighbours simply keep the results
	they already had and a rebuild reconciles them.
	"""

	def __init__(
		self, uow: UnitOfWork, knowledge_items: KnowledgeItemRepository,
		computation: SimilarityComputation,
	) -> None:
		self.uow = uow
		self.knowledge_items = knowledge_items
		self.computation = computation

	async def handle(self, command: RefreshNeighborSimilarityCommand) -> int:
		"""Returns how many neighbours were recomputed, purely so the caller can say so in a log
		line -- there is no read model over this and nothing waits on the result."""
		neighbor_ids = await self.uow.similarity_results.similar_ticket_ids_for_source(
			command.source_ticket_id
		)
		if not neighbor_ids:
			return 0

		# One round trip for every neighbour's vector, then every search, all before a transaction
		# is opened. The graph write is the only part that needs to be transactional, and holding a
		# transaction open across a hop's worth of round trips to the vector store buys nothing --
		# the same reason the rebuild computes a whole page before opening one.
		#
		# The source ticket is not in this list and is never refreshed here: it is the one ticket
		# whose results were just computed against the current corpus.
		items = await self.knowledge_items.get_by_source_ids(neighbor_ids)
		computed = [
			(item.source_id, await self.computation.results_for(item, command.generated_at))
			for item in items
		]

		# Each neighbour's results are swapped wholesale, so a neighbour is never left holding a
		# half-written set; the commit then makes the whole hop land or none of it.
		for source_id, results in computed:
			await self.uow.similarity_results.replace_for_source(source_id, results)

		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise

		return len(computed)
