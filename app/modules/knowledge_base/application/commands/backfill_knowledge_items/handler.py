from __future__ import annotations

import logging
from uuid import UUID

from app.modules.knowledge_base.application.commands.backfill_knowledge_items.command import (
	BackfillKnowledgeItemsCommand,
)
from app.modules.knowledge_base.application.dto.backfill_report_dto import BackfillReportDTO
from app.modules.knowledge_base.application.services.corpus_ingestion import CorpusIngestion
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository

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

	Resumable and idempotent by construction: it embeds only what has no knowledge item, writes per
	batch, and pages by ticket id. Re-running it after any interruption -- or after new tickets
	arrive -- costs one query per batch and does only the work still outstanding.

	Touches one store only, which is why it takes no UnitOfWork at all: a backfill produces
	knowledge items and nothing else, and the similarity graph those items imply is built afterwards
	by a separate pass. A batch is durable as soon as it is written, so an interrupted run keeps
	everything up to the last completed batch without any transaction to reason about.
	"""

	def __init__(
		self,
		knowledge_items: KnowledgeItemRepository,
		ticket_read_repository: TicketReadRepository,
		ingestion: CorpusIngestion,
	) -> None:
		self.knowledge_items = knowledge_items
		self.ticket_read_repository = ticket_read_repository
		self.ingestion = ingestion

	async def handle(self, command: BackfillKnowledgeItemsCommand) -> BackfillReportDTO:
		# Ahead of everything else, and shared with every other path that adds to the corpus: it
		# resolves the model, fails immediately if the provider is unreachable or serving the wrong
		# build rather than in the twentieth minute of a run, and refuses to add to a corpus some
		# other model produced.
		await self.ingestion.prepare(self.knowledge_items)

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

			existing = await self.knowledge_items.existing_source_ids([ticket.id for ticket in page])
			already_embedded += len(existing)

			items = []
			for ticket in page:
				if ticket.id in existing:
					continue
				item = await self.ingestion.item_for(ticket, command.generated_at)
				if item is None:
					skipped_empty_text += 1
					continue
				items.append(item)

			if items:
				# One write for the whole batch rather than one per item: a write is a network
				# round trip now, so the per-item loop this replaced would have made the store,
				# not the embedding model, the slow part of a long pass.
				await self.knowledge_items.add_many(items)
				embedded += len(items)

			logger.info(
				"Backfill progress: %d tickets seen, %d embedded, %d already present, %d skipped",
				tickets_seen, embedded, already_embedded, skipped_empty_text,
			)

		return BackfillReportDTO(
			tickets_seen=tickets_seen, already_embedded=already_embedded,
			embedded=embedded, skipped_empty_text=skipped_empty_text,
		)
