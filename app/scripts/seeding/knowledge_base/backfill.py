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
from app.modules.knowledge_base.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.knowledge_base.infrastructure.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from app.modules.knowledge_base.infrastructure.vector_store.client import close_qdrant_client, get_qdrant_client
from app.modules.knowledge_base.infrastructure.vector_store.collection import COLLECTION_NAME, ensure_collection
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_knowledge_item_repository import (
	QdrantKnowledgeItemRepository,
)
from app.modules.knowledge_base.infrastructure.vector_store.qdrant_similarity_search import QdrantSimilaritySearch
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)
from app.shared.config.settings import get_settings
from app.shared.database.engine import engine
from app.shared.database.session import create_session

logger = logging.getLogger("knowledge_base.backfill")

PROVISION = "provision"
BACKFILL = "backfill"
REBUILD = "rebuild"


async def run_provision() -> None:
	"""Creates the Qdrant collection and its payload indexes if they are not already there.

	The vector store's counterpart of `alembic upgrade head`, and the reason it is a stage of this
	script rather than something the application does on startup: provisioning is a deliberate act
	with a reviewable outcome, and the API must not depend on an external service being reachable
	the moment it boots. Idempotent, so it leads every run by default and costs two reads once the
	collection exists.
	"""
	report = await ensure_collection(get_qdrant_client())
	if report.collection_created:
		logger.info("Created Qdrant collection %r.", COLLECTION_NAME)
	else:
		logger.info("Qdrant collection %r already exists.", COLLECTION_NAME)
	if report.indexes_created:
		logger.info("Created payload indexes: %s.", ", ".join(report.indexes_created))


async def reset_derived_data() -> None:
	"""Drops the corpus and the graph so the next pass rebuilds both from scratch.

	Safe to expose as a flag because everything it deletes is derived: knowledge items are
	recomputable from the tickets they were built from, and the graph from the items. Nothing here
	is a source of truth, so this destroys no information -- it only costs the time to recompute.
	The one situation that genuinely requires it is a model change, where every stored vector
	becomes incomparable with every new one at once.

	Two stores, so two deletions with no transaction spanning them. The order is the safe one: the
	graph goes first, because a graph pointing at vectors that no longer exist is the state this is
	trying to leave, whereas a corpus that has briefly lost its graph is simply a corpus awaiting a
	rebuild -- which is exactly what the next stage does.
	"""
	async with SqlAlchemyUnitOfWork() as uow:
		await uow.similarity_results.delete_all()
		await uow.commit()
	await QdrantKnowledgeItemRepository(get_qdrant_client()).delete_all()
	logger.warning("Reset: all similarity results and knowledge items deleted.")


async def run_backfill(batch_size: int) -> None:
	provider = OllamaEmbeddingProvider.from_settings()
	session = create_session()
	try:
		handler = BackfillKnowledgeItemsHandler(
			knowledge_items=QdrantKnowledgeItemRepository(get_qdrant_client()),
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
	qdrant = get_qdrant_client()
	handler = RebuildSimilarityGraphHandler(
		uow_factory=SqlAlchemyUnitOfWork,
		knowledge_items=QdrantKnowledgeItemRepository(qdrant),
		search_port=QdrantSimilaritySearch(qdrant),
	)
	report = await handler.handle(
		RebuildSimilarityGraphCommand(generated_at=datetime.now(UTC), batch_size=batch_size)
	)

	logger.info(
		"Rebuild complete: %d items processed, %d results written, %d sources with no match above "
		"the threshold.",
		report.items_processed, report.results_written, report.sources_without_results,
	)


async def run(*, stages: list[str], reset: bool, batch_size: int) -> None:
	settings = get_settings()
	logger.info("Embedding endpoint: %s", settings.ollama_host)
	logger.info("Vector store: %s", settings.qdrant_url)

	started = time.monotonic()
	try:
		# Provisioning is unconditional rather than a stage you opt into, even though --only lists
		# it: everything below reads or writes a collection that has to exist, --reset included, and
		# it is idempotent and costs two reads once it does. `--only provision` therefore means
		# "provision and stop", which is the only reason it needs a name at all.
		await run_provision()
		if reset:
			await reset_derived_data()
		# Backfill before rebuild is not a preference: the graph is derived from the corpus, so
		# rebuilding first would compute neighbours over an incomplete corpus and be stale the
		# moment it finished.
		if BACKFILL in stages:
			await run_backfill(batch_size)
		if REBUILD in stages:
			await run_rebuild(batch_size)
	finally:
		logger.info("Finished in %.1fs", time.monotonic() - started)
		await engine.dispose()
		await close_qdrant_client()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		prog="python -m app.scripts.seeding.knowledge_base.backfill",
		description=(
			"Provision the Qdrant collection, populate the knowledge base from tickets already in "
			"the database, then derive the similarity graph. Every stage is safe to re-run: "
			"provisioning creates only what is missing, the backfill embeds only tickets that have "
			"no vector yet, and the rebuild replaces each source's results wholesale."
		),
		epilog=(
			"Two endpoints are involved. The embedding endpoint comes from OLLAMA_HOST (default "
			"http://localhost:11434) and, for a hosted endpoint, OLLAMA_API_KEY: to embed on "
			"another machine's GPU while the database stays here, point OLLAMA_HOST at it -- that "
			"machine's Ollama must be started with OLLAMA_HOST=0.0.0.0 to accept anything other "
			"than loopback connections, and must have the model pulled. The vector store comes "
			"from QDRANT_CLUSTER_ENDPOINT and QDRANT_API_KEY. Similarity results stay in Postgres, "
			"so DATABASE_URL is still needed for every stage but provisioning."
		),
	)
	parser.add_argument(
		"--only", choices=[PROVISION, BACKFILL, REBUILD], default=None,
		help="Run a single stage. Default is all three, in the order listed.",
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
	stages = [args.only] if args.only else [PROVISION, BACKFILL, REBUILD]
	asyncio.run(run(stages=stages, reset=args.reset, batch_size=args.batch_size))


if __name__ == "__main__":
	main()
