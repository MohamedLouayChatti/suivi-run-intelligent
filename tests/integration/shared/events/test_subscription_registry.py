"""
Integration tests for ``SubscriptionRegistry``.

Verifies that the registry stores, retrieves, and removes handlers
correctly, and that registration order is preserved.
"""
from __future__ import annotations

import pytest

from app.shared.events.event import DomainEvent
from app.shared.events.handler import EventHandler
from app.shared.events.subscriptions import SubscriptionRegistry


# ---------------------------------------------------------------------------
# Minimal test events and handlers
# ---------------------------------------------------------------------------


class EventA(DomainEvent):
    pass


class EventB(DomainEvent):
    pass


class HandlerOne(EventHandler):
    async def handle(self, event: DomainEvent) -> None:
        pass


class HandlerTwo(EventHandler):
    async def handle(self, event: DomainEvent) -> None:
        pass


class HandlerThree(EventHandler):
    async def handle(self, event: DomainEvent) -> None:
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSubscribe:
    def test_subscribe_and_retrieve_single_handler(self, subscription_registry: SubscriptionRegistry):
        # Arrange
        handler = HandlerOne()

        # Act
        subscription_registry.subscribe(EventA, handler)
        handlers = subscription_registry.get_handlers(EventA)

        # Assert
        assert handler in handlers

    def test_multiple_handlers_for_same_event(self, subscription_registry: SubscriptionRegistry):
        # Arrange
        h1 = HandlerOne()
        h2 = HandlerTwo()

        # Act
        subscription_registry.subscribe(EventA, h1)
        subscription_registry.subscribe(EventA, h2)
        handlers = subscription_registry.get_handlers(EventA)

        # Assert
        assert h1 in handlers
        assert h2 in handlers
        assert len(handlers) == 2

    def test_registration_order_is_preserved(self, subscription_registry: SubscriptionRegistry):
        # Arrange
        h1 = HandlerOne()
        h2 = HandlerTwo()
        h3 = HandlerThree()

        # Act
        subscription_registry.subscribe(EventA, h1)
        subscription_registry.subscribe(EventA, h2)
        subscription_registry.subscribe(EventA, h3)
        handlers = subscription_registry.get_handlers(EventA)

        # Assert — insertion order must be maintained
        assert handlers == [h1, h2, h3]

    def test_handlers_for_different_events_are_independent(self, subscription_registry: SubscriptionRegistry):
        # Arrange
        h_a = HandlerOne()
        h_b = HandlerTwo()

        # Act
        subscription_registry.subscribe(EventA, h_a)
        subscription_registry.subscribe(EventB, h_b)

        # Assert
        assert subscription_registry.get_handlers(EventA) == [h_a]
        assert subscription_registry.get_handlers(EventB) == [h_b]


class TestGetHandlers:
    def test_unregistered_event_returns_empty_list(self, subscription_registry: SubscriptionRegistry):
        # Act
        handlers = subscription_registry.get_handlers(EventA)

        # Assert
        assert handlers == []

    def test_get_handlers_returns_copy(self, subscription_registry: SubscriptionRegistry):
        """Mutating the returned list must not affect the registry."""
        # Arrange
        h = HandlerOne()
        subscription_registry.subscribe(EventA, h)

        # Act
        handlers = subscription_registry.get_handlers(EventA)
        handlers.clear()

        # Assert — registry still has the handler
        assert len(subscription_registry.get_handlers(EventA)) == 1


class TestUnsubscribe:
    def test_unsubscribe_removes_handler(self, subscription_registry: SubscriptionRegistry):
        # Arrange
        h = HandlerOne()
        subscription_registry.subscribe(EventA, h)

        # Act
        subscription_registry.unsubscribe(EventA, h)

        # Assert
        assert subscription_registry.get_handlers(EventA) == []

    def test_unsubscribe_unknown_handler_does_not_raise(self, subscription_registry: SubscriptionRegistry):
        # Arrange — handler was never subscribed
        h = HandlerOne()

        # Act / Assert — must not raise
        subscription_registry.unsubscribe(EventA, h)

    def test_unsubscribe_unknown_event_does_not_raise(self, subscription_registry: SubscriptionRegistry):
        # Arrange — event was never subscribed to at all
        h = HandlerOne()

        # Act / Assert — must not raise
        subscription_registry.unsubscribe(EventB, h)

    def test_unsubscribe_one_of_two_handlers(self, subscription_registry: SubscriptionRegistry):
        # Arrange
        h1 = HandlerOne()
        h2 = HandlerTwo()
        subscription_registry.subscribe(EventA, h1)
        subscription_registry.subscribe(EventA, h2)

        # Act
        subscription_registry.unsubscribe(EventA, h1)

        # Assert
        handlers = subscription_registry.get_handlers(EventA)
        assert h1 not in handlers
        assert h2 in handlers
