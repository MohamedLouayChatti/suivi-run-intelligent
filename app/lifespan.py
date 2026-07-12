from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from app.modules.ticket_management import bootstrap as ticket_management_bootstrap
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry


@asynccontextmanager
async def lifespan(app: Any) -> AsyncIterator[None]:
	registry = SubscriptionRegistry()
	event_bus = InMemoryEventBus(registry)

	app.state.subscription_registry = registry
	app.state.event_bus = event_bus

	ticket_management_bootstrap.register_subscriptions(registry)

	yield
