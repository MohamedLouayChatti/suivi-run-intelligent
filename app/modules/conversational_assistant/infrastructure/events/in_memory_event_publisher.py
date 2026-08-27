from __future__ import annotations

from app.shared.events.event import DomainEvent
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.event_publisher import EventPublisher


class InMemoryEventPublisher(EventPublisher):
	def __init__(self, event_bus: InMemoryEventBus) -> None:
		self._event_bus = event_bus

	async def publish(self, event: DomainEvent) -> None:
		await self._event_bus.publish(event)
