from __future__ import annotations

from abc import ABC, abstractmethod

from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)


class SimilarityRecalculationScheduleRepository(ABC):
	"""The single configured recalculation schedule, if one has been saved.

	There is no `id` anywhere on this contract because there is only ever one schedule for the
	installation -- asking for it by identity would invent an identity nobody has.
	"""

	@abstractmethod
	async def get(self) -> SimilarityRecalculationSchedule | None:
		"""The saved schedule, or None if no administrator has configured one.

		None is a real answer rather than an error, and callers substitute
		`SimilarityRecalculationSchedule.default()` for it. That is what keeps the default in code:
		an installation nobody has configured has no row, so there is nothing to seed and nothing
		that can disagree with the constants.
		"""
		raise NotImplementedError

	@abstractmethod
	async def save(self, schedule: SimilarityRecalculationSchedule) -> None:
		"""Store `schedule` as the configured one, replacing whatever was there.

		Upsert rather than add/update, since the caller changing the schedule has no reason to know
		whether anyone has ever changed it before.
		"""
		raise NotImplementedError
