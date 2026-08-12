from __future__ import annotations

from app.modules.knowledge_base.application.dto.similarity_result_row_dto import SimilarityResultRowDTO
from app.modules.knowledge_base.domain.entities.knowledge_item import KnowledgeItem
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.infrastructure.persistence.models.knowledge_item_model import KnowledgeItemModel
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_result_model import SimilarityResultModel


def knowledge_item_to_model(item: KnowledgeItem) -> KnowledgeItemModel:
	return KnowledgeItemModel(
		id=item.id,
		source_type=item.source_type,
		source_id=item.source_id,
		application=item.application,
		embedding=item.embedding,
		embedding_model=item.embedding_model,
		embedding_model_version=item.embedding_model_version,
		generated_at=item.generated_at,
	)


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
