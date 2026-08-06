from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.application.interfaces.unit_of_work import UnitOfWork
from app.modules.notifications.infrastructure.persistence.repositories.sqlalchemy_notification_repository import SqlAlchemyNotificationRepository
from app.shared.database.session import create_session


class SqlAlchemyUnitOfWork(UnitOfWork):
	def __init__(self, session: AsyncSession | None = None) -> None:
		self.session = session or create_session()
		self.notifications = SqlAlchemyNotificationRepository(self.session)

	async def commit(self) -> None:
		await self.session.commit()

	async def rollback(self) -> None:
		await self.session.rollback()

	async def close(self) -> None:
		await self.session.close()

	async def __aenter__(self) -> Self:
		return self

	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc: BaseException | None,
		tb: TracebackType | None,
	) -> None:
		if exc_type is not None:
			await self.rollback()

		await self.close()
