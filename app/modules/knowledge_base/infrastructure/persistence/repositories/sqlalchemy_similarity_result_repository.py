from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.domain.repositories.similarity_result_repository import SimilarityResultRepository
from app.modules.knowledge_base.infrastructure.persistence import mapper
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_result_model import SimilarityResultModel


class SqlAlchemySimilarityResultRepository(SimilarityResultRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def replace_for_source(self, source_ticket_id: UUID, results: list[SimilarityResult]) -> None:
		await self.session.execute(
			delete(SimilarityResultModel).where(SimilarityResultModel.source_ticket_id == source_ticket_id)
		)
		for result in results:
			self.session.add(mapper.similarity_result_to_model(result))

	async def similar_ticket_ids_for_source(self, source_ticket_id: UUID) -> list[UUID]:
		result = await self.session.execute(
			select(SimilarityResultModel.similar_ticket_id)
			.where(SimilarityResultModel.source_ticket_id == source_ticket_id)
			.order_by(SimilarityResultModel.rank)
		)
		return list(result.scalars().all())

	async def delete_all(self) -> None:
		await self.session.execute(delete(SimilarityResultModel))
