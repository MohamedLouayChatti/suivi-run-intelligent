from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.interfaces.unit_of_work import UnitOfWork
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_permission_repository import SqlAlchemyPermissionRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_role_repository import SqlAlchemyRoleRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.shared.database.session import create_session


class SqlAlchemyUnitOfWork(UnitOfWork):
	def __init__(self, session: AsyncSession | None = None) -> None:
		self.session = session or create_session()
		self.users = SqlAlchemyUserRepository(self.session)
		self.roles = SqlAlchemyRoleRepository(self.session)
		self.permissions = SqlAlchemyPermissionRepository(self.session)

	async def commit(self) -> None:
		await self.session.commit()

	async def rollback(self) -> None:
		await self.session.rollback()

	async def close(self) -> None:
		await self.session.close()

	async def __aenter__(self) -> Self:
		return self

	async def __aexit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
		if exc_type is not None:
			await self.rollback()
		await self.close()
