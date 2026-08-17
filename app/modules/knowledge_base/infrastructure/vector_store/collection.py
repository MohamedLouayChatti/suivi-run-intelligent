from __future__ import annotations

from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient, models

from app.modules.knowledge_base.infrastructure.embedding_model import EMBEDDING_DIMENSIONS

# The single collection every knowledge source shares. One collection rather than one per
# Application, which is also what Qdrant's own multi-tenancy guidance recommends: many small
# collections each carry their own segments and index structures, while one collection with an
# indexed tenant key lets the engine keep each tenant's points together and search only those.
# Documentation, when it becomes the second source, joins this same collection under a different
# `source_type` rather than getting one of its own -- retrieval is meant to span sources.
COLLECTION_NAME = "knowledge_items"

# Payload keys, named once. Both the repository (which writes them) and the search adapter (which
# filters on them) reference these rather than string literals: a filter on a misspelled key is not
# an error in Qdrant, it simply matches nothing, which would look exactly like "no similar tickets".
SOURCE_TYPE = "source_type"
SOURCE_ID = "source_id"
APPLICATION = "application"
EMBEDDING_MODEL = "embedding_model"
EMBEDDING_MODEL_VERSION = "embedding_model_version"
GENERATED_AT = "generated_at"
IDENTIFIERS = "identifiers"
REFERENCE_KEYS = "reference_keys"
GENERGY_ID = "genergy_id"
OCEANE_ID = "oceane_id"

# Only fields something actually filters or facets on are indexed. An unused payload index is not
# free -- it is built on every upsert and held in memory -- so `source_type`, `embedding_model`,
# `generated_at` and `oceane_id` are stored and returned but deliberately left unindexed until
# something queries them.
_PAYLOAD_INDEXES: tuple[tuple[str, models.PayloadSchemaType | models.KeywordIndexParams], ...] = (
	# is_tenant marks this as the partitioning key: Qdrant then stores each application's points
	# together and confines a filtered search to that tenant's own subgraph. This is what makes the
	# hard application filter cheap instead of a penalty, and it is the direct answer to the
	# filtered-search limitation the previous pgvector index carried as a known deferred problem --
	# there, the filter was applied after the index had already picked its candidates, so a narrow
	# filter could quietly return fewer results than exist.
	(APPLICATION, models.KeywordIndexParams(type=models.KeywordIndexType.KEYWORD, is_tenant=True)),
	# Filtered on twice: to find which tickets are already embedded, and to exclude the query's own
	# ticket from its results.
	(SOURCE_ID, models.PayloadSchemaType.KEYWORD),
	# The two halves of the reference lookup -- a cited identifier resolves against either the
	# referenced ticket's own genergy_id or an identifier extracted from its description.
	(GENERGY_ID, models.PayloadSchemaType.KEYWORD),
	(REFERENCE_KEYS, models.PayloadSchemaType.KEYWORD),
	# Faceted, not filtered: the maintenance passes ask which distinct model builds are present
	# before they touch anything.
	(EMBEDDING_MODEL_VERSION, models.PayloadSchemaType.KEYWORD),
)


@dataclass(frozen=True)
class ProvisioningReport:
	"""What `ensure_collection` actually had to do, so a provisioning run can say whether it
	created anything or found everything already in place."""

	collection_created: bool
	indexes_created: list[str]


async def ensure_collection(client: AsyncQdrantClient) -> ProvisioningReport:
	"""Create the collection and its payload indexes if they are not already there.

	This is the Qdrant counterpart of `alembic upgrade head`, and it is deliberately an explicit
	step rather than something the application does at startup or a repository does lazily on first
	write. Startup must not depend on an external service being reachable, and a schema decision
	buried in a hot path is one nobody reviews.

	Idempotent by construction: existing indexes are read back off the collection rather than
	blindly recreated, so re-running this is a couple of reads and no writes.

	The vector size and distance metric come from the pinned embedding model, never from settings.
	They are this store's equivalent of a fixed column width: a collection built for 1024 cosine
	dimensions and a threshold calibrated against cosine scores from that same model are only valid
	as a set.
	"""
	collection_created = False
	if not await client.collection_exists(COLLECTION_NAME):
		await client.create_collection(
			collection_name=COLLECTION_NAME,
			vectors_config=models.VectorParams(
				size=EMBEDDING_DIMENSIONS, distance=models.Distance.COSINE
			),
		)
		collection_created = True

	info = await client.get_collection(COLLECTION_NAME)
	already_indexed = set(info.payload_schema or {})

	indexes_created = []
	for field_name, field_schema in _PAYLOAD_INDEXES:
		if field_name in already_indexed:
			continue
		await client.create_payload_index(
			collection_name=COLLECTION_NAME, field_name=field_name, field_schema=field_schema,
		)
		indexes_created.append(field_name)

	return ProvisioningReport(collection_created=collection_created, indexes_created=indexes_created)
