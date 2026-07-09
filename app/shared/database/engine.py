from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.shared.config.settings import get_settings


settings = get_settings()

engine: AsyncEngine = create_async_engine(
	settings.database_url,
	echo=False,
	pool_pre_ping=True,
	pool_recycle=1800,
	pool_size=5,
	max_overflow=10,
	pool_timeout=30,
)
