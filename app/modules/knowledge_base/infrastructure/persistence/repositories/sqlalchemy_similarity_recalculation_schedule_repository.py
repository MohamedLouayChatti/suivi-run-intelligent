from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)
from app.modules.knowledge_base.domain.repositories.similarity_recalculation_schedule_repository import (
	SimilarityRecalculationScheduleRepository,
)
from app.modules.knowledge_base.infrastructure.persistence.mapper import (
	apply_recalculation_schedule_to_model,
	model_to_recalculation_schedule,
	recalculation_schedule_to_model,
)
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_recalculation_schedule_model import (
	SINGLETON_ID,
	SimilarityRecalculationScheduleModel,
)


class SqlAlchemySimilarityRecalculationScheduleRepository(SimilarityRecalculationScheduleRepository):
	"""Reads and writes the one schedule row. Owns no session lifecycle and never commits -- the
	unit of work does that, as everywhere else in this module."""

	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get(self) -> SimilarityRecalculationSchedule | None:
		model = await self.session.get(SimilarityRecalculationScheduleModel, SINGLETON_ID)
		return model_to_recalculation_schedule(model) if model is not None else None

	async def save(self, schedule: SimilarityRecalculationSchedule) -> None:
		# Read-then-write rather than a dialect-specific upsert: this is a single row written by an
		# administrator pressing save, so the extra round trip costs nothing, and it keeps the
		# insert and update paths in ordinary mapper functions instead of in SQL.
		model = await self.session.get(SimilarityRecalculationScheduleModel, SINGLETON_ID)
		if model is None:
			self.session.add(recalculation_schedule_to_model(schedule))
		else:
			apply_recalculation_schedule_to_model(schedule, model)
