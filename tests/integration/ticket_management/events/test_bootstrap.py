"""
Integration tests for the Ticket Management bootstrap hook.

``register_subscriptions()`` is the module's public bootstrap entry point.
At the current project stage, Ticket Management only produces events — it
does not consume any — so calling ``register_subscriptions`` must leave the
registry empty.

These tests document and lock in that expected behaviour.
"""
from __future__ import annotations

import pytest

from app.modules.ticket_management.bootstrap import register_subscriptions
from app.shared.events.subscriptions import SubscriptionRegistry


class TestRegisterSubscriptions:
    def test_does_not_raise(self, subscription_registry: SubscriptionRegistry):
        """Calling the bootstrap hook must complete without raising."""
        # Act / Assert
        register_subscriptions(subscription_registry)

    def test_registers_no_handlers(self, subscription_registry: SubscriptionRegistry):
        """
        Ticket Management currently only publishes events and does not
        subscribe to any.  The registry must remain empty after bootstrap.
        """
        # Act
        register_subscriptions(subscription_registry)

        # Assert — internal dict should be empty (no subscriptions registered)
        assert len(subscription_registry._subscriptions) == 0

    def test_returns_none(self, subscription_registry: SubscriptionRegistry):
        """The hook must return None (no implicit return value)."""
        # Act
        result = register_subscriptions(subscription_registry)

        # Assert
        assert result is None

    def test_is_idempotent(self, subscription_registry: SubscriptionRegistry):
        """
        Calling ``register_subscriptions`` twice must not raise and must
        produce the same (empty) result.
        """
        # Act
        register_subscriptions(subscription_registry)
        register_subscriptions(subscription_registry)

        # Assert — still empty
        assert len(subscription_registry._subscriptions) == 0

    def test_accepts_fresh_registry(self):
        """Bootstrap must work with any ``SubscriptionRegistry`` instance."""
        # Arrange
        fresh_registry = SubscriptionRegistry()

        # Act / Assert
        register_subscriptions(fresh_registry)
        assert len(fresh_registry._subscriptions) == 0
