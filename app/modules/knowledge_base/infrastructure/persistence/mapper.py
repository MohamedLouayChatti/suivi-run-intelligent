from __future__ import annotations

from uuid import uuid4

from app.modules.knowledge_base.application.dto.similarity_result_row_dto import SimilarityResultRowDTO
from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem, TicketKnowledgeItem
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.domain.services.description_preprocessor import ExtractedIdentifier
from app.modules.knowledge_base.infrastructure.persistence.models.knowledge_item_model import (
	KnowledgeItemIdentifierModel,
	KnowledgeItemModel,
	TicketKnowledgeItemModel,
)
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_result_model import SimilarityResultModel


def knowledge_item_to_model(item: KnowledgeItem) -> KnowledgeItemModel:
	"""Maps to the ORM subtype matching the domain subtype. Identifier rows are built here and
	cascade-inserted with the parent, so persisting an item never needs a second call.
	"""
	identifiers = [
		KnowledgeItemIdentifierModel(id=uuid4(), identifier_type=extracted.type, value=extracted.value)
		for extracted in item.identifiers
	]
	shared = {
		"id": item.id,
		"source_type": item.source_type,
		"source_id": item.source_id,
		"application": item.application,
		"embedding": item.embedding,
		"embedding_model": item.embedding_model,
		"embedding_model_version": item.embedding_model_version,
		"generated_at": item.generated_at,
		"identifiers": identifiers,
	}

	if isinstance(item, TicketKnowledgeItem):
		return TicketKnowledgeItemModel(**shared, genergy_id=item.genergy_id, oceane_id=item.oceane_id)

	# KnowledgeItem is the abstraction, never a persistable row of its own: `knowledge_items` is
	# discriminated by source_type and every row belongs to a subtype table. Failing loudly here
	# is what will surface the missing mapping when the documentation source is added.
	raise NotImplementedError(f"No persistence mapping for knowledge item type {type(item).__name__}")


def model_to_knowledge_item(model: KnowledgeItemModel) -> KnowledgeItem:
	"""The inverse of `knowledge_item_to_model`, for the passes that read the corpus back rather
	than adding to it (rebuilding the similarity graph from stored vectors, without re-embedding).

	Dispatches on the ORM subtype for the same reason the forward direction dispatches on the
	domain subtype: `knowledge_items` is discriminated, and a row always belongs to exactly one
	subtype table.
	"""
	identifiers = [
		ExtractedIdentifier(type=row.identifier_type, value=row.value) for row in model.identifiers
	]
	shared = {
		"id": model.id,
		"source_id": model.source_id,
		"application": model.application,
		"embedding": list(model.embedding),
		"embedding_model": model.embedding_model,
		"embedding_model_version": model.embedding_model_version,
		"generated_at": model.generated_at,
		"identifiers": identifiers,
	}

	if isinstance(model, TicketKnowledgeItemModel):
		return TicketKnowledgeItem.create(**shared, genergy_id=model.genergy_id, oceane_id=model.oceane_id)

	raise NotImplementedError(f"No domain mapping for knowledge item row of type {type(model).__name__}")


def similarity_result_to_model(result: SimilarityResult) -> SimilarityResultModel:
	return SimilarityResultModel(
		id=result.id,
		source_ticket_id=result.source_ticket_id,
		similar_ticket_id=result.similar_ticket_id,
		similarity_score=result.similarity_score,
		rank=result.rank,
		generated_at=result.generated_at,
		embedding_model_version=result.embedding_model_version,
		algorithm_version=result.algorithm_version,
	)


def model_to_similarity_result_row_dto(model: SimilarityResultModel) -> SimilarityResultRowDTO:
	return SimilarityResultRowDTO(
		similar_ticket_id=model.similar_ticket_id,
		similarity_score=model.similarity_score,
		rank=model.rank,
	)
