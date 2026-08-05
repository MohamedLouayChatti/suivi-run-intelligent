from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.modules.ticket_management import bootstrap as ticket_management_bootstrap
from app.modules.auth import bootstrap as auth_bootstrap
from app.modules.audit import bootstrap as audit_bootstrap
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
	registry = SubscriptionRegistry()
	event_bus = InMemoryEventBus(registry)

	app.state.subscription_registry = registry
	app.state.event_bus = event_bus
	instance_authorization_registry = InstanceAuthorizationRegistry()
	app.state.instance_authorization_registry = instance_authorization_registry

	ticket_management_bootstrap.register_subscriptions(registry)
	auth_bootstrap.register_subscriptions(registry)
	audit_bootstrap.register_subscriptions(registry)

	ticket_management_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	auth_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	audit_bootstrap.register_instance_authorization_policies(instance_authorization_registry)

	yield
