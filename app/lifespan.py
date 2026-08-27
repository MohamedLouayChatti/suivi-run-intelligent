from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.modules.ticket_management import bootstrap as ticket_management_bootstrap
from app.modules.auth import bootstrap as auth_bootstrap
from app.modules.audit import bootstrap as audit_bootstrap
from app.modules.notifications import bootstrap as notifications_bootstrap
from app.modules.analytics import bootstrap as analytics_bootstrap
from app.modules.knowledge_base import bootstrap as knowledge_base_bootstrap
from app.modules.conversational_assistant import bootstrap as conversational_assistant_bootstrap
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry
from app.workers.worker import job_queue, job_scheduler


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
	notifications_bootstrap.register_subscriptions(registry)
	analytics_bootstrap.register_subscriptions(registry, event_bus)
	knowledge_base_bootstrap.register_subscriptions(registry, event_bus)
	# Also takes instance_authorization_registry (unlike its siblings above): the agent runner
	# bound here needs it so tools can authorize resource-level access exactly as HTTP routes do.
	conversational_assistant_bootstrap.register_subscriptions(registry, event_bus, instance_authorization_registry)

	ticket_management_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	auth_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	audit_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	notifications_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	analytics_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	knowledge_base_bootstrap.register_instance_authorization_policies(instance_authorization_registry)
	conversational_assistant_bootstrap.register_instance_authorization_policies(instance_authorization_registry)

	# Recurring work is registered before the scheduler starts, so nothing can fire against a
	# half-built registration. Knowledge Base's hook is async because it reads the configured
	# schedule from the database, which is where an administrator's changes live between
	# restarts; Analytics' is async too, for shape parity, even though its schedule is a fixed
	# constant in code with nothing to read.
	await knowledge_base_bootstrap.register_scheduled_jobs(job_scheduler)
	await analytics_bootstrap.register_scheduled_jobs(job_scheduler)
	await job_scheduler.start()

	yield

	# The clock stops first, so nothing new can fire while in-flight work is being cancelled.
	await job_scheduler.shutdown()
	# Background jobs are cancelled rather than drained: everything enqueued today is recomputable
	# work whose loss a rebuild repairs, and draining would make every shutdown wait on remote
	# services. Nothing else here needs teardown -- the registries and the bus are plain objects.
	await job_queue.shutdown()
