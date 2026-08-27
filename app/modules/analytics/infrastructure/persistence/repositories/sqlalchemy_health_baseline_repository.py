from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.domain.repositories.health_baseline_repository import HealthBaselineRepository
from app.modules.analytics.domain.value_objects.application_health_baseline import ApplicationHealthBaseline
from app.modules.analytics.infrastructure.persistence.models.application_health_baseline_model import (
	ApplicationHealthBaselineModel,
)
from app.modules.ticket_management.domain.enums.application import Application


class SqlAlchemyHealthBaselineRepository(HealthBaselineRepository):
	"""Read-then-write, like Knowledge Base's schedule repository: a row per application, only
	ever written once a day by the recalculation job, so the extra round trip costs nothing."""

	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get(self, application: Application) -> ApplicationHealthBaseline | None:
		model = await self.session.get(ApplicationHealthBaselineModel, application)
		return _to_domain(model) if model is not None else None

	async def get_all(self) -> dict[Application, ApplicationHealthBaseline]:
		rows = (await self.session.execute(select(ApplicationHealthBaselineModel))).scalars().all()
		return {model.application: _to_domain(model) for model in rows}

	async def upsert(self, baseline: ApplicationHealthBaseline) -> None:
		model = await self.session.get(ApplicationHealthBaselineModel, baseline.application)
		if model is None:
			self.session.add(_to_model(baseline))
		else:
			_apply(baseline, model)


def _to_domain(model: ApplicationHealthBaselineModel) -> ApplicationHealthBaseline:
	return ApplicationHealthBaseline(
		application=model.application,
		active_count_mean=model.active_count_mean,
		active_count_median=model.active_count_median,
		active_count_max=model.active_count_max,
		active_count_stddev=model.active_count_stddev,
		active_count_sample_days=model.active_count_sample_days,
		resolution_hours_mean=model.resolution_hours_mean,
		resolution_hours_median=model.resolution_hours_median,
		resolution_hours_max=model.resolution_hours_max,
		resolution_hours_stddev=model.resolution_hours_stddev,
		resolution_hours_sample_count=model.resolution_hours_sample_count,
		computed_at=model.computed_at,
	)


def _to_model(baseline: ApplicationHealthBaseline) -> ApplicationHealthBaselineModel:
	model = ApplicationHealthBaselineModel(application=baseline.application)
	_apply(baseline, model)
	return model


def _apply(baseline: ApplicationHealthBaseline, model: ApplicationHealthBaselineModel) -> None:
	model.active_count_mean = baseline.active_count_mean
	model.active_count_median = baseline.active_count_median
	model.active_count_max = baseline.active_count_max
	model.active_count_stddev = baseline.active_count_stddev
	model.active_count_sample_days = baseline.active_count_sample_days
	model.resolution_hours_mean = baseline.resolution_hours_mean
	model.resolution_hours_median = baseline.resolution_hours_median
	model.resolution_hours_max = baseline.resolution_hours_max
	model.resolution_hours_stddev = baseline.resolution_hours_stddev
	model.resolution_hours_sample_count = baseline.resolution_hours_sample_count
	model.computed_at = baseline.computed_at
