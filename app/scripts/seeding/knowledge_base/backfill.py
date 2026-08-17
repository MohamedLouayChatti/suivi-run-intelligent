from __future__ import annotations

import argparse
import asyncio
import logging
import time
from datetime import UTC, datetime

from app.modules.knowledge_base.application.commands.backfill_knowledge_items.command import (
	BackfillKnowledgeItemsCommand,
)
from app.modules.knowledge_base.application.commands.backfill_knowledge_items.handler import (
	BackfillKnowledgeItemsHandler,
)
from app.modules.knowledge_base.application.commands.rebuild_similarity_graph.command import (
	RebuildSimilarityGraphCommand,
)
from app.modules.knowledge_base.application.commands.rebuild_similarity_graph.handler import (
	RebuildSimilarityGraphHandler,
)
from app.modules.knowledge_base.infrastructure.persistence.repositories.pgvector_similarity_search import (
	PgvectorSimilaritySearch,
)
from app.modules.knowledge_base.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.knowledge_base.infrastructure.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)
from app.shared.config.settings import get_settings
from app.shared.database.engine import engine
from app.shared.database.session import create_session

logger = logging.getLogger("knowledge_base.backfill")

BACKFILL = "backfill"
REBUILD = "rebuild"


async def reset_derived_data() -> None:
	"""Drops the corpus and the graph so the next pass rebuilds both from scratch.

	Safe to expose as a flag because everything it deletes is derived: knowledge items are
	recomputable from the tickets they were built from, and the graph from the items. Nothing here
	is a source of truth, so this destroys no information -- it only costs the time to recompute.
	The one situation that genuinely requires it is a model change, where every stored vector
	becomes incomparable with every new one at once.
	"""
	async with SqlAlchemyUnitOfWork() as uow:
		await uow.similarity_results.delete_all()
		await uow.knowledge_items.delete_all()
		await uow.commit()
	logger.warning("Reset: all knowledge items and similarity results deleted.")


async def run_backfill(batch_size: int) -> None:
	provider = OllamaEmbeddingProvider.from_settings()
	session = create_session()
	try:
		handler = BackfillKnowledgeItemsHandler(
			uow_factory=SqlAlchemyUnitOfWork,
			ticket_read_repository=SqlAlchemyTicketReadRepository(session),
			embedding_provider=provider,
		)
		report = await handler.handle(
			BackfillKnowledgeItemsCommand(generated_at=datetime.now(UTC), batch_size=batch_size)
		)
	finally:
		await session.close()

	logger.info(
		"Backfill complete: %d tickets seen, %d newly embedded, %d already present, "
		"%d skipped (nothing to embed after preprocessing).",
		report.tickets_seen, report.embedded, report.already_embedded, report.skipped_empty_text,
	)


async def run_rebuild(batch_size: int) -> None:
	session = create_session()
	try:
		handler = RebuildSimilarityGraphHandler(
			uow_factory=SqlAlchemyUnitOfWork,
			search_port=PgvectorSimilaritySearch(session),
		)
		report = await handler.handle(
			RebuildSimilarityGraphCommand(generated_at=datetime.now(UTC), batch_size=batch_size)
		)
	finally:
		await session.close()

	logger.info(
		"Rebuild complete: %d items processed, %d results written, %d sources with no match above "
		"the threshold.",
		report.items_processed, report.results_written, report.sources_without_results,
	)


async def run(*, stages: list[str], reset: bool, batch_size: int) -> None:
	settings = get_settings()
	logger.info("Embedding endpoint: %s", settings.ollama_host)

	if reset:
		await reset_derived_data()

	started = time.monotonic()
	try:
		# Order is not a preference: the graph is derived from the corpus, so rebuilding before
		# backfilling would compute neighbours over an incomplete corpus and immediately be stale.
		if BACKFILL in stages:
			await run_backfill(batch_size)
		if REBUILD in stages:
			await run_rebuild(batch_size)
	finally:
		logger.info("Finished in %.1fs", time.monotonic() - started)
		await engine.dispose()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		prog="python -m app.scripts.seeding.knowledge_base.backfill",
		description=(
			"Populate the knowledge base from tickets already in the database, then derive the "
			"similarity graph. Both stages are safe to re-run: the backfill embeds only what is "
			"missing, and the rebuild replaces each source's results wholesale."
		),
		epilog=(
			"The embedding endpoint comes from OLLAMA_HOST (default http://localhost:11434) and, "
			"for a hosted endpoint, OLLAMA_API_KEY. To embed on another machine's GPU while the "
			"database stays here, point OLLAMA_HOST at it -- only the embedding requests cross the "
			"network. That machine's Ollama must be started with OLLAMA_HOST=0.0.0.0 to accept "
			"anything other than loopback connections, and must have the model pulled."
		),
	)
	parser.add_argument(
		"--only", choices=[BACKFILL, REBUILD], default=None,
		help="Run a single stage. Default is both, backfill first.",
	)
	parser.add_argument(
		"--reset", action="store_true",
		help=(
			"Delete every knowledge item and similarity result first. Needed after an embedding "
			"model change, when previously stored vectors are no longer comparable to new ones."
		),
	)
	parser.add_argument(
		"--batch-size", type=int, default=25,
		help=(
			"Rows per transaction (default: 25). For the backfill this is also how much embedding "
			"work an interrupted run loses, since a batch is committed as a unit."
		),
	)
	return parser.parse_args(argv)


def main() -> None:
	logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s | %(message)s")
	args = parse_args()
	stages = [args.only] if args.only else [BACKFILL, REBUILD]
	asyncio.run(run(stages=stages, reset=args.reset, batch_size=args.batch_size))


if __name__ == "__main__":
	main()
