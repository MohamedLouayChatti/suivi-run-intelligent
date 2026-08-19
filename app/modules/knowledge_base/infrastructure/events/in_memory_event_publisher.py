from __future__ import annotations

from app.shared.events.event import DomainEvent
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.event_publisher import EventPublisher


class InMemoryEventPublisher(EventPublisher):
	"""This module's own adapter over the shared bus, mirroring Auth's and Ticket Management's.

	Its own rather than borrowed: until now this module reached into Ticket Management's
	Infrastructure for one, which is the single import module boundaries forbid outright, and it
	went unnoticed only because the class is four lines long. Now that this module publishes events
	of its own rather than relaying one, it owns the adapter it publishes them through.
	"""

	def __init__(self, event_bus: InMemoryEventBus) -> None:
		self._event_bus = event_bus

	async def publish(self, event: DomainEvent) -> None:
		await self._event_bus.publish(event)
