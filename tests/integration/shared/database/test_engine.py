"""
Integration tests for the shared async engine.

These tests verify *our* infrastructure configuration — that the engine
was created correctly and can reach the database — not SQLAlchemy internals.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.shared.database.engine import engine


class TestEngineCreation:
    def test_engine_is_not_none(self):
        # Arrange / Act / Assert
        assert engine is not None

    def test_engine_is_async_engine(self):
        assert isinstance(engine, AsyncEngine)

    def test_engine_has_correct_dialect(self):
        # The application uses asyncpg (PostgreSQL).
        assert engine.dialect.name == "postgresql"


class TestEngineConnectivity:
    async def test_engine_can_connect(self):
        # Arrange / Act
        async with engine.connect() as conn:
            # Assert — no exception means connection succeeded
            assert conn is not None
        await engine.dispose()  # Clean up the connection pool after the test

    async def test_engine_connection_executes_select_one(self):
        # Arrange / Act
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            scalar = result.scalar()
        # Assert
        assert scalar == 1
        await engine.dispose()  # Clean up the connection pool after the test

    async def test_engine_multiple_connections_succeed(self):
        # Arrange / Act / Assert — open two connections sequentially
        async with engine.connect() as conn1:
            r1 = await conn1.execute(text("SELECT 1"))
            assert r1.scalar() == 1

        async with engine.connect() as conn2:
            r2 = await conn2.execute(text("SELECT 2"))
            assert r2.scalar() == 2
        await engine.dispose()  # Clean up the connection pool after the test
