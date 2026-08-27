from __future__ import annotations

from app.modules.analytics.infrastructure.events.handlers.analytics_event_handler import AnalyticsEventHandler
from app.modules.analytics.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.modules.analytics.infrastructure.jobs.health_baseline_recalculation_job import (
	HEALTH_BASELINE_RECALCULATION_JOB_NAME,
	HEALTH_BASELINE_SCHEDULE,
	recalculate_application_health_baselines,
)
from app.modules.ticket_management.domain.events.ticket_archived import TicketArchived
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.modules.ticket_management.domain.events.ticket_restored import TicketRestored
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.modules.ticket_management.domain.events.ticket_transferred import TicketTransferred
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry
from app.workers.jobs import JobScheduler
from app.workers.worker import job_queue


def register_subscriptions(registry: SubscriptionRegistry, event_bus: InMemoryEventBus) -> None:
	"""Analytics' first subscriptions, and its first publisher -- it is no longer a pure
	reporting/read module that only reaches into the operational database from the outside.

	Takes `event_bus` (the second module's register_subscriptions to do so, after Knowledge
	Base) because AnalyticsEventHandler needs an EventPublisher of its own to announce
	ApplicationHealthBecameCritical, built here at subscription time the same way Knowledge
	Base's is.
	"""
	handler = AnalyticsEventHandler(
		event_publisher=InMemoryEventPublisher(event_bus),
		# The process-wide runner, injected rather than imported inside the handler -- same
		# reasoning as Knowledge Base's own event handler.
		job_queue=job_queue,
	)
	for event_type in (TicketCreated, TicketStatusChanged, TicketArchived, TicketRestored, TicketTransferred):
		registry.subscribe(event_type, handler)


async def register_scheduled_jobs(scheduler: JobScheduler) -> None:
	"""Registers the daily application-health baseline recalculation.

	Async to match the shape every register_scheduled_jobs hook has, even though this one reads
	nothing from the database at startup: the schedule is a fixed constant in code, not an
	admin-configurable row, so there is no persisted configuration to re-register from.
	"""
	await scheduler.register(
		recalculate_application_health_baselines,
		name=HEALTH_BASELINE_RECALCULATION_JOB_NAME,
		schedule=HEALTH_BASELINE_SCHEDULE,
		enabled=True,
	)


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Still no per-resource instance authorization: the admin overview is gated by
	analytics.read_any_application, list/report endpoints by the application-collection scope,
	and neither a cached baseline nor a health status has a resource_id anyone is authorized
	against."""
	return None
