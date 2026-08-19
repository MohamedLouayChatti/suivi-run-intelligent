from __future__ import annotations

from app.modules.knowledge_base.application.dto.similarity_result_row_dto import SimilarityResultRowDTO
from app.modules.knowledge_base.domain.entities.similarity_recalculation_schedule import (
	SimilarityRecalculationSchedule,
)
from app.modules.knowledge_base.domain.entities.similarity_result import SimilarityResult
from app.modules.knowledge_base.domain.enums.weekday import Weekday
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_recalculation_schedule_model import (
	SINGLETON_ID,
	SimilarityRecalculationScheduleModel,
)
from app.modules.knowledge_base.infrastructure.persistence.models.similarity_result_model import SimilarityResultModel

# This module's two relational things are mapped here: the similarity graph, and the schedule that
# rebuilds it. Knowledge items are not relational rows at all -- they are points in the vector
# store, and their translation lives in infrastructure/vector_store/payload.py, which is the same
# job against a different shape.


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


def recalculation_schedule_to_model(
	schedule: SimilarityRecalculationSchedule,
) -> SimilarityRecalculationScheduleModel:
	return SimilarityRecalculationScheduleModel(
		id=SINGLETON_ID,
		**_recalculation_schedule_columns(schedule),
	)


def apply_recalculation_schedule_to_model(
	schedule: SimilarityRecalculationSchedule, model: SimilarityRecalculationScheduleModel,
) -> None:
	"""Write a schedule onto the row that already holds one.

	The counterpart of the function above for the update path, rather than building a detached
	model and merging it: the row's identity is a constant, so the only thing an update has to do
	is set the columns on the instance the session already has.
	"""
	for column, value in _recalculation_schedule_columns(schedule).items():
		setattr(model, column, value)


def model_to_recalculation_schedule(
	model: SimilarityRecalculationScheduleModel,
) -> SimilarityRecalculationSchedule:
	# Constructed directly rather than through `create`: these values were validated when they were
	# saved, and a stored row that no longer satisfies the invariants (a timezone this machine
	# cannot resolve, say) must be readable so it can be corrected, not unreadable.
	return SimilarityRecalculationSchedule(
		enabled=model.enabled,
		days_of_week=frozenset(Weekday(day) for day in model.days_of_week),
		hour=model.hour,
		minute=model.minute,
		timezone=model.timezone,
		updated_at=model.updated_at,
		updated_by=model.updated_by,
	)


def _recalculation_schedule_columns(schedule: SimilarityRecalculationSchedule) -> dict[str, object]:
	"""The column values one schedule implies, shared by the insert and the update paths so the two
	cannot fall out of step as fields are added."""
	return {
		"enabled": schedule.enabled,
		# Stored in week order rather than set order, so the column reads the way it is displayed
		# and two equal schedules produce identical rows.
		"days_of_week": [day.value for day in schedule.days_in_week_order()],
		"hour": schedule.hour,
		"minute": schedule.minute,
		"timezone": schedule.timezone,
		"updated_at": schedule.updated_at,
		"updated_by": schedule.updated_by,
	}
