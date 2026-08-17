from __future__ import annotations

from app.modules.knowledge_base.application.dto.similarity_result_row_dto import SimilarityResultRowDTO
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_result_model import SimilarityResultModel

# Only the similarity graph is mapped here. Knowledge items are not relational rows at all -- they
# are points in the vector store, and their translation lives in infrastructure/vector_store/
# payload.py, which is the same job against a different shape.


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
