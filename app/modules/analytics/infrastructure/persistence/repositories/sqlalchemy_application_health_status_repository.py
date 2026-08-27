from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.domain.repositories.application_health_status_repository import (
	ApplicationHealthStatusRepository,
)
from app.modules.analytics.domain.value_objects.application_health_status import ApplicationHealthStatus
from app.modules.analytics.infrastructure.persistence.models.application_health_status_model import (
	ApplicationHealthStatusModel,
)
from app.modules.ticket_management.domain.enums.application import Application


class SqlAlchemyApplicationHealthStatusRepository(ApplicationHealthStatusRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get(self, application: Application) -> ApplicationHealthStatus | None:
		model = await self.session.get(ApplicationHealthStatusModel, application)
		return _to_domain(model) if model is not None else None

	async def upsert(self, status: ApplicationHealthStatus) -> None:
		model = await self.session.get(ApplicationHealthStatusModel, status.application)
		if model is None:
			self.session.add(_to_model(status))
		else:
			_apply(status, model)


def _to_domain(model: ApplicationHealthStatusModel) -> ApplicationHealthStatus:
	return ApplicationHealthStatus(
		application=model.application, health_level=model.health_level,
		active_tickets=model.active_tickets, avg_resolution_hours=model.avg_resolution_hours,
		updated_at=model.updated_at,
	)


def _to_model(status: ApplicationHealthStatus) -> ApplicationHealthStatusModel:
	model = ApplicationHealthStatusModel(application=status.application)
	_apply(status, model)
	return model


def _apply(status: ApplicationHealthStatus, model: ApplicationHealthStatusModel) -> None:
	model.health_level = status.health_level
	model.active_tickets = status.active_tickets
	model.avg_resolution_hours = status.avg_resolution_hours
	model.updated_at = status.updated_at
