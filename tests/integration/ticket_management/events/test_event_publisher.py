"""
Integration tests for ``InMemoryEventPublisher``.

Verifies that the publisher correctly delegates to ``InMemoryEventBus``
and that events reach their registered handlers.

Fake handlers are concrete ``EventHandler`` subclasses — no mocks.
"""
from __future__ import annotations

import pytest

from app.modules.ticket_management.infrastructure.events.in_memory_event_publisher import (
    InMemoryEventPublisher,
)
from app.shared.events.event import DomainEvent
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.handler import EventHandler
from app.shared.events.subscriptions import SubscriptionRegistry


# ---------------------------------------------------------------------------
# Minimal test events and fake handlers
# ---------------------------------------------------------------------------


class SomethingHappened(DomainEvent):
    pass


class AnotherThingHappened(DomainEvent):
    pass


class RecordingHandler(EventHandler):
    def __init__(self) -> None:
        self.received: list[DomainEvent] = []

    async def handle(self, event: DomainEvent) -> None:
        self.received.append(event)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInMemoryEventPublisher:
    def _make_publisher(self, handler: EventHandler | None = None, event_type: type[DomainEvent] = SomethingHappened):
        registry = SubscriptionRegistry()
        if handler is not None:
            registry.subscribe(event_type, handler)
        bus = InMemoryEventBus(registry)
        return InMemoryEventPublisher(bus)

    async def test_published_event_reaches_registered_handler(self):
        # Arrange
        handler = RecordingHandler()
        publisher = self._make_publisher(handler)
        event = SomethingHappened()

        # Act
        await publisher.publish(event)

        # Assert
        assert len(handler.received) == 1
        assert handler.received[0] is event

    async def test_published_event_is_correct_instance(self):
        # Arrange
        handler = RecordingHandler()
        publisher = self._make_publisher(handler)
        event = SomethingHappened()

        # Act
        await publisher.publish(event)

        # Assert
        assert handler.received[0] is event

    async def test_multiple_events_all_dispatched(self):
        # Arrange
        handler = RecordingHandler()
        publisher = self._make_publisher(handler)

        events = [SomethingHappened(), SomethingHappened(), SomethingHappened()]

        # Act
        for evt in events:
            await publisher.publish(evt)

        # Assert
        assert len(handler.received) == 3
        assert handler.received == events

    async def test_publish_with_no_subscribers_does_not_raise(self):
        # Arrange — no handler registered
        publisher = self._make_publisher(handler=None)

        # Act / Assert — must not raise
        await publisher.publish(SomethingHappened())

    async def test_publish_different_event_types_independently(self):
        # Arrange
        handler_a = RecordingHandler()
        handler_b = RecordingHandler()

        registry = SubscriptionRegistry()
        registry.subscribe(SomethingHappened, handler_a)
        registry.subscribe(AnotherThingHappened, handler_b)
        bus = InMemoryEventBus(registry)
        publisher = InMemoryEventPublisher(bus)

        event_a = SomethingHappened()
        event_b = AnotherThingHappened()

        # Act
        await publisher.publish(event_a)
        await publisher.publish(event_b)

        # Assert — each handler only received its own event type
        assert handler_a.received == [event_a]
        assert handler_b.received == [event_b]

    async def test_publisher_uses_fixtures(
        self,
        event_publisher: InMemoryEventPublisher,
        subscription_registry: SubscriptionRegistry,
    ):
        """Verify the root conftest fixtures wire up correctly."""
        # Arrange — register a handler on the shared registry
        handler = RecordingHandler()
        subscription_registry.subscribe(SomethingHappened, handler)
        event = SomethingHappened()

        # Act
        await event_publisher.publish(event)

        # Assert
        assert handler.received == [event]
