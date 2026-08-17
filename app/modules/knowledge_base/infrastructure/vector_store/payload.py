from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from qdrant_client import models

from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem, TicketKnowledgeItem
from app.modules.knowledge_base.domain.enums.identifier_type import IdentifierType
from app.modules.knowledge_base.domain.enums.knowledge_source_type import KnowledgeSourceType
from app.modules.knowledge_base.domain.services.description_preprocessor import ExtractedIdentifier
from app.modules.knowledge_base.infrastructure.vector_store import collection
from app.modules.ticket_management.domain.enums.application import Application


def reference_key(identifier: ExtractedIdentifier) -> str:
	"""The single composite form a reference identifier is stored and queried under.

	A reference match is a match on the *pair* (type, value) -- an incident number and an order
	number that happen to share digits are not the same object. Relationally that was a two-column
	index and a tuple IN; here the pair is flattened into one keyword so the lookup stays a single
	indexed MatchAny instead of a nested per-element filter. Both sides of the comparison go
	through this function, which is what keeps the written form and the queried form from drifting.
	"""
	return f"{identifier.type.value}:{identifier.value}"


def knowledge_item_to_point(item: KnowledgeItem) -> models.PointStruct:
	"""Maps a domain item onto the point that represents it.

	The item's own id is the point id, not its source_id: a knowledge item is its own entity with
	its own identity, and collapsing the two would quietly assume one item per source forever --
	which is only true while nothing is chunked.

	What used to be joined-table inheritance is now payload shape: `source_type` discriminates, and
	the source-specific keys are simply present or absent. The schema-level guarantee that a
	document row could never carry a ticket's genergy_id is gone with the subtype table, so it is
	enforced here instead -- this function writes those keys only for the subtype that owns them.
	"""
	payload: dict[str, Any] = {
		collection.SOURCE_TYPE: item.source_type.value,
		collection.SOURCE_ID: str(item.source_id),
		collection.APPLICATION: item.application.value,
		collection.EMBEDDING_MODEL: item.embedding_model,
		collection.EMBEDDING_MODEL_VERSION: item.embedding_model_version,
		collection.GENERATED_AT: item.generated_at.isoformat(),
		# The full extracted set is stored because the rebuild pass reads items back and re-runs
		# their reference search from them, so it has to be able to reconstruct every identifier --
		# not only the ones today's retrieval policy happens to query on.
		collection.IDENTIFIERS: [
			{"type": extracted.type.value, "value": extracted.value} for extracted in item.identifiers
		],
		# Derived and denormalized purely so the reference filter is one indexed lookup. Only the
		# reference families are here: the rest co-occur across unrelated tickets and were measured
		# to pull in false matches if they guaranteed a result slot.
		collection.REFERENCE_KEYS: [
			reference_key(extracted) for extracted in item.identifiers if extracted.type.is_reference
		],
	}

	if isinstance(item, TicketKnowledgeItem):
		payload[collection.GENERGY_ID] = item.genergy_id
		payload[collection.OCEANE_ID] = item.oceane_id
		return models.PointStruct(id=str(item.id), vector=item.embedding, payload=payload)

	# KnowledgeItem is the abstraction, never a stored point of its own -- every item belongs to a
	# source subtype. Failing loudly here is what will surface the missing mapping when the
	# documentation source arrives.
	raise NotImplementedError(f"No vector-store mapping for knowledge item type {type(item).__name__}")


def point_to_knowledge_item(point: models.Record | models.ScoredPoint) -> KnowledgeItem:
	"""The inverse, for the rebuild pass that reads the corpus back rather than adding to it.

	Requires the point to have been fetched with its vector: the whole point of a rebuild is to
	re-derive the graph from vectors already stored, without paying to embed anything again.
	"""
	payload = point.payload or {}
	source_type = KnowledgeSourceType(payload[collection.SOURCE_TYPE])

	if point.vector is None:
		raise ValueError(
			f"Point {point.id} was fetched without its vector; reading knowledge items back "
			f"requires with_vectors=True."
		)

	shared = {
		"id": UUID(str(point.id)),
		"source_id": UUID(payload[collection.SOURCE_ID]),
		"application": Application(payload[collection.APPLICATION]),
		"embedding": list(point.vector),
		"embedding_model": payload[collection.EMBEDDING_MODEL],
		"embedding_model_version": payload[collection.EMBEDDING_MODEL_VERSION],
		"generated_at": datetime.fromisoformat(payload[collection.GENERATED_AT]),
		"identifiers": [
			ExtractedIdentifier(type=IdentifierType(entry["type"]), value=entry["value"])
			for entry in payload.get(collection.IDENTIFIERS, [])
		],
	}

	if source_type is KnowledgeSourceType.TICKET:
		return TicketKnowledgeItem.create(
			**shared,
			genergy_id=payload.get(collection.GENERGY_ID),
			oceane_id=payload.get(collection.OCEANE_ID),
		)

	raise NotImplementedError(f"No domain mapping for a knowledge item of source type {source_type}")
