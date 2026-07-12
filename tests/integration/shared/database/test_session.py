"""
Integration tests for the shared async session factory.

These tests verify our session infrastructure configuration — that sessions
are created correctly with the configured defaults — not SQLAlchemy internals.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database.session import create_session


class TestSessionFactoryCreation:
    def test_create_session_returns_async_session(self):
        # Arrange / Act
        session = create_session()
        # Assert
        assert isinstance(session, AsyncSession)

    def test_two_sessions_are_distinct_objects(self):
        # Arrange / Act
        s1 = create_session()
        s2 = create_session()
        # Assert
        assert s1 is not s2

    async def test_sessions_are_independent(self):
        """Each session should have its own identity map."""
        # Arrange / Act / Assert
        s1 = create_session()
        s2 = create_session()
        try:
            assert s1.identity_map is not s2.identity_map
        finally:
            await s1.close()
            await s2.close()


class TestSessionLifecycle:
    async def test_session_can_execute_query(self):
        # Arrange
        session = create_session()
        # Act / Assert
        try:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        finally:
            await session.close()

    async def test_session_closes_cleanly(self):
        # Arrange
        session = create_session()
        # Act / Assert — close must not raise
        await session.close()

    async def test_session_rollback_does_not_raise(self):
        # Arrange
        session = create_session()
        try:
            await session.execute(text("SELECT 1"))
            # Act / Assert — rolling back a clean session must not raise
            await session.rollback()
        finally:
            await session.close()
