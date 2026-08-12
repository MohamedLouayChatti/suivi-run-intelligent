from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_base.application.dto.similarity_result_row_dto import SimilarityResultRowDTO
from app.modules.knowledge_base.application.interfaces.similarity_read_repository import SimilarityReadRepository
from app.modules.knowledge_base.infrastructure.persistence import mapper
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_result_model import SimilarityResultModel


class SqlAlchemySimilarityReadRepository(SimilarityReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_for_source(self, source_ticket_id: UUID) -> list[SimilarityResultRowDTO]:
		stmt = (
			select(SimilarityResultModel)
			.where(SimilarityResultModel.source_ticket_id == source_ticket_id)
			.order_by(SimilarityResultModel.rank)
		)
		result = await self.session.scalars(stmt)
		return [mapper.model_to_similarity_result_row_dto(model) for model in result.all()]
