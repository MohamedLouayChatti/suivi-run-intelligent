from __future__ import annotations

import logging

from app.shared.events.event import DomainEvent
from app.shared.events.subscriptions import SubscriptionRegistry


logger = logging.getLogger(__name__)


class InMemoryEventBus:
	def __init__(self, registry: SubscriptionRegistry) -> None:
		self._registry = registry

	async def publish(self, event: DomainEvent) -> None:
		event_type = type(event)
		for handler in self._registry.get_handlers(event_type):
			try:
				await handler.handle(event)
			except Exception:
				logger.exception(
					"Failed to handle %s with %s",
					event_type.__name__,
					handler.__class__.__name__,
				)
