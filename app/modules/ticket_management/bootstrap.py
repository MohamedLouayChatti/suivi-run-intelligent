from __future__ import annotations

from app.shared.events.subscriptions import SubscriptionRegistry


def register_subscriptions(registry: SubscriptionRegistry) -> None:
	"""Register Ticket Management event consumers.

	Ticket Management currently only produces events, so it does not
	subscribe to any shared events yet. The function exists as the module's
	public bootstrap hook and will be extended when the module starts
	consuming events from other modules.
	"""
	return None
