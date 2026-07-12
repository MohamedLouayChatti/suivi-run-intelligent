"""
Integration tests for ``InMemoryEventBus``.

Fake handlers are concrete ``EventHandler`` subclasses defined here — no
mocks.  Each handler records the events it receives so tests can assert on
call order, call count, and the exact event instances passed.
"""
from __future__ import annotations

import pytest

from app.shared.events.event import DomainEvent
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.handler import EventHandler
from app.shared.events.subscriptions import SubscriptionRegistry


# ---------------------------------------------------------------------------
# Minimal test events
# ---------------------------------------------------------------------------


class OrderPlaced(DomainEvent):
    pass


class OrderCancelled(DomainEvent):
    pass


# ---------------------------------------------------------------------------
# Fake handlers
# ---------------------------------------------------------------------------


class RecordingHandler(EventHandler):
    """Records every event it handles, in order."""

    def __init__(self) -> None:
        self.received: list[DomainEvent] = []

    async def handle(self, event: DomainEvent) -> None:
        self.received.append(event)


class FailingHandler(EventHandler):
    """Always raises to simulate a broken handler."""

    async def handle(self, event: DomainEvent) -> None:
        raise RuntimeError("handler failure")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_bus_with_handlers(*handlers: EventHandler, event_type: type[DomainEvent] = OrderPlaced) -> InMemoryEventBus:
    registry = SubscriptionRegistry()
    for h in handlers:
        registry.subscribe(event_type, h)
    return InMemoryEventBus(registry)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSingleHandler:
    async def test_single_handler_is_called(self):
        # Arrange
        handler = RecordingHandler()
        bus = make_bus_with_handlers(handler)
        event = OrderPlaced()

        # Act
        await bus.publish(event)

        # Assert
        assert len(handler.received) == 1

    async def test_correct_event_instance_is_passed(self):
        # Arrange
        handler = RecordingHandler()
        bus = make_bus_with_handlers(handler)
        event = OrderPlaced()

        # Act
        await bus.publish(event)

        # Assert
        assert handler.received[0] is event


class TestMultipleHandlers:
    async def test_multiple_handlers_all_called(self):
        # Arrange
        h1 = RecordingHandler()
        h2 = RecordingHandler()
        bus = make_bus_with_handlers(h1, h2)
        event = OrderPlaced()

        # Act
        await bus.publish(event)

        # Assert
        assert len(h1.received) == 1
        assert len(h2.received) == 1

    async def test_handlers_called_in_registration_order(self):
        # Arrange
        call_order: list[str] = []

        class TaggedHandler(EventHandler):
            def __init__(self, tag: str) -> None:
                self.tag = tag

            async def handle(self, event: DomainEvent) -> None:
                call_order.append(self.tag)

        h1 = TaggedHandler("first")
        h2 = TaggedHandler("second")
        h3 = TaggedHandler("third")
        registry = SubscriptionRegistry()
        for h in (h1, h2, h3):
            registry.subscribe(OrderPlaced, h)
        bus = InMemoryEventBus(registry)

        # Act
        await bus.publish(OrderPlaced())

        # Assert
        assert call_order == ["first", "second", "third"]

    async def test_each_handler_receives_same_event_instance(self):
        # Arrange
        h1 = RecordingHandler()
        h2 = RecordingHandler()
        bus = make_bus_with_handlers(h1, h2)
        event = OrderPlaced()

        # Act
        await bus.publish(event)

        # Assert
        assert h1.received[0] is event
        assert h2.received[0] is event


class TestNoSubscribers:
    async def test_publishing_with_no_subscribers_does_not_raise(self):
        # Arrange — empty registry, no subscribers
        bus = InMemoryEventBus(SubscriptionRegistry())
        event = OrderPlaced()

        # Act / Assert — must complete silently
        await bus.publish(event)

    async def test_publishing_different_event_type_does_not_call_handler(self):
        # Arrange — handler subscribed to OrderPlaced only
        handler = RecordingHandler()
        registry = SubscriptionRegistry()
        registry.subscribe(OrderPlaced, handler)
        bus = InMemoryEventBus(registry)

        # Act — publish a different event
        await bus.publish(OrderCancelled())

        # Assert — handler must not have been called
        assert handler.received == []


class TestFaultTolerance:
    async def test_failing_handler_does_not_stop_remaining_handlers(self):
        """
        When handler A raises, the bus must log the failure and still
        invoke handler B.
        """
        # Arrange
        failing = FailingHandler()
        recording = RecordingHandler()
        registry = SubscriptionRegistry()
        registry.subscribe(OrderPlaced, failing)
        registry.subscribe(OrderPlaced, recording)
        bus = InMemoryEventBus(registry)
        event = OrderPlaced()

        # Act — must not raise
        await bus.publish(event)

        # Assert — the recording handler still ran
        assert len(recording.received) == 1
        assert recording.received[0] is event

    async def test_failing_handler_does_not_propagate_exception(self):
        """``bus.publish`` must not raise even when a handler raises."""
        # Arrange
        bus = make_bus_with_handlers(FailingHandler())

        # Act / Assert — no exception must escape
        await bus.publish(OrderPlaced())
