from __future__ import annotations

import logging
from collections.abc import Callable
from uuid import UUID, uuid4

from app.modules.knowledge_base.application.commands.backfill_knowledge_items.command import (
	BackfillKnowledgeItemsCommand,
)
from app.modules.knowledge_base.application.dto.backfill_report_dto import BackfillReportDTO
from app.modules.knowledge_base.application.exceptions import MixedEmbeddingCorpus
from app.modules.knowledge_base.application.interfaces.unit_of_work import UnitOfWork
from app.modules.knowledge_base.domain.entities.knowledge_item import TicketKnowledgeItem
from app.modules.knowledge_base.domain.services.description_preprocessor import preprocess_description
from app.modules.ticket_management.application.dto.ticket_dto import TicketContentDTO
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.shared.ai.embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


class BackfillKnowledgeItemsHandler:
	"""Populates knowledge items for tickets that predate this module.

	The counterpart of GenerateSimilarityResultsHandler for tickets that never fired a TicketCreated
	anyone was listening to. It represents each ticket identically -- the same
	`preprocess_description`, the same provider, the same entity -- so a backfilled ticket and a
	live-ingested one are indistinguishable afterwards. Deliberately does *not* generate similarity
	results: a backfilled ticket's neighbours are mostly tickets this pass has not embedded yet, so
	searching as it goes would produce a graph that depends on the order the corpus happened to be
	traversed in. The graph is built afterwards, once, by RebuildSimilarityGraphHandler.

	Resumable and idempotent by construction: it embeds only what has no knowledge item, commits per
	batch, and pages by ticket id. Re-running it after any interruption -- or after new tickets
	arrive -- costs one query per batch and does only the work still outstanding.

	Takes a `uow_factory` rather than a UnitOfWork because a full pass is a sequence of independent
	transactions, not one long one: an interrupted run must keep the batches it already committed,
	and a transaction must never be held open across a model call.
	"""

	def __init__(
		self,
		uow_factory: Callable[[], UnitOfWork],
		ticket_read_repository: TicketReadRepository,
		embedding_provider: EmbeddingProvider,
	) -> None:
		self.uow_factory = uow_factory
		self.ticket_read_repository = ticket_read_repository
		self.embedding_provider = embedding_provider

	async def handle(self, command: BackfillKnowledgeItemsCommand) -> BackfillReportDTO:
		# Ahead of everything else: this resolves the model and fails immediately if the provider
		# is unreachable or serving the wrong build, rather than in the twentieth minute of a run.
		# It is also what makes model_name/model_version readable below.
		await self.embedding_provider.warm_up()
		await self._assert_corpus_matches_provider()

		tickets_seen = already_embedded = embedded = skipped_empty_text = 0
		after_id: UUID | None = None

		while True:
			page = await self.ticket_read_repository.list_ticket_contents(
				after_id=after_id, limit=command.batch_size
			)
			if not page:
				break
			after_id = page[-1].id
			tickets_seen += len(page)

			async with self.uow_factory() as uow:
				existing = await uow.knowledge_items.existing_source_ids([ticket.id for ticket in page])
			already_embedded += len(existing)

			items = []
			for ticket in page:
				if ticket.id in existing:
					continue
				item = await self._embed(ticket, command)
				if item is None:
					skipped_empty_text += 1
					continue
				items.append(item)

			if items:
				async with self.uow_factory() as uow:
					for item in items:
						await uow.knowledge_items.add(item)
					await uow.commit()
				embedded += len(items)

			logger.info(
				"Backfill progress: %d tickets seen, %d embedded, %d already present, %d skipped",
				tickets_seen, embedded, already_embedded, skipped_empty_text,
			)

		return BackfillReportDTO(
			tickets_seen=tickets_seen, already_embedded=already_embedded,
			embedded=embedded, skipped_empty_text=skipped_empty_text,
		)

	async def _embed(
		self, ticket: TicketContentDTO, command: BackfillKnowledgeItemsCommand
	) -> TicketKnowledgeItem | None:
		"""Returns None for a ticket with nothing left to embed.

		Preprocessing can empty a description outright -- one consisting only of an order reference
		becomes a bare placeholder. Embedding that would store a vector for "a commande was
		mentioned", which is a near-neighbour of every other such ticket and of nothing meaningful,
		so the ticket is left without a knowledge item instead. A later pass picks it up for free if
		it ever gains real text.
		"""
		preprocessed = preprocess_description(ticket.description)
		if not preprocessed.embedding_text.strip():
			logger.debug("Skipping ticket %s: nothing left to embed after preprocessing", ticket.id)
			return None

		embedding = await self.embedding_provider.embed(preprocessed.embedding_text)
		return TicketKnowledgeItem.create(
			id=uuid4(), source_id=ticket.id, application=ticket.application, embedding=embedding,
			embedding_model=self.embedding_provider.model_name,
			embedding_model_version=self.embedding_provider.model_version,
			generated_at=command.generated_at, identifiers=list(preprocessed.identifiers),
			genergy_id=ticket.genergy_id, oceane_id=ticket.oceane_id,
		)

	async def _assert_corpus_matches_provider(self) -> None:
		"""Adding to a corpus built by a different model is the one way this pass can do damage,
		and the damage is invisible afterwards -- hence a check up front rather than a repair later.
		"""
		async with self.uow_factory() as uow:
			present = await uow.knowledge_items.distinct_model_versions()
		expected = (self.embedding_provider.model_name, self.embedding_provider.model_version)
		if any(pair != expected for pair in present):
			raise MixedEmbeddingCorpus(present, expected)
