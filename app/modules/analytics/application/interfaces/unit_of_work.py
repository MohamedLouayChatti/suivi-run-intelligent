from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from app.modules.analytics.domain.repositories.application_health_status_repository import (
	ApplicationHealthStatusRepository,
)
from app.modules.analytics.domain.repositories.health_baseline_repository import HealthBaselineRepository


class UnitOfWork(ABC):
	"""Analytics' first Unit of Work -- covers the two tables this module now owns rather than
	only reads: the cached per-application baseline and the last known health tier."""

	health_baselines: HealthBaselineRepository
	health_statuses: ApplicationHealthStatusRepository

	@abstractmethod
	async def commit(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def rollback(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def close(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def __aenter__(self) -> Self:
		raise NotImplementedError

	@abstractmethod
	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc: BaseException | None,
		tb: TracebackType | None,
	) -> None:
		raise NotImplementedError
