from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.shared.database.engine import engine


async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
	bind=engine,
	autoflush=False,
	class_=AsyncSession,
	expire_on_commit=False,
)


def create_session() -> AsyncSession:
	return async_session_factory()
