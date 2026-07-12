from __future__ import annotations

from app.shared.events.event import DomainEvent
from app.shared.events.handler import EventHandler


class SubscriptionRegistry:
	def __init__(self) -> None:
		self._subscriptions: dict[type[DomainEvent], list[EventHandler]] = {}

	def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
		self._subscriptions.setdefault(event_type, []).append(handler)

	def unsubscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
		handlers = self._subscriptions.get(event_type)
		if not handlers:
			return

		try:
			handlers.remove(handler)
		except ValueError:
			return

		if not handlers:
			del self._subscriptions[event_type]

	def get_handlers(self, event_type: type[DomainEvent]) -> list[EventHandler]:
		return list(self._subscriptions.get(event_type, []))
