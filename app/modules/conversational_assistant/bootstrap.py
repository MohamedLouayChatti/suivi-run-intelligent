from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.modules.conversational_assistant.application.interfaces.conversation_read_repository import (
	ConversationReadRepository,
)
from app.modules.conversational_assistant.application.security.agent_run_access_policy import AgentRunAccessPolicy
from app.modules.conversational_assistant.application.security.conversation_access_policy import (
	ConversationAccessPolicy,
)
from app.modules.conversational_assistant.infrastructure.events.in_memory_event_publisher import (
	InMemoryEventPublisher,
)
from app.modules.conversational_assistant.infrastructure.jobs.agent_run_runner import agent_run_runner
from app.modules.conversational_assistant.infrastructure.persistence.repositories.sqlalchemy_conversation_read_repository import (
	SqlAlchemyConversationReadRepository,
)
from app.shared.database.session import create_session
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


@asynccontextmanager
async def _conversation_read_repository_scope() -> AsyncIterator[ConversationReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyConversationReadRepository(session)
	finally:
		await session.close()


def register_subscriptions(
	registry: SubscriptionRegistry,
	event_bus: InMemoryEventBus,
	instance_authorization_registry: InstanceAuthorizationRegistry,
) -> None:
	"""This module subscribes to no other module's events in v1 -- SendMessageHandler enqueues
	the agent run directly (mirrors Knowledge Base's TriggerSimilarityRecalculationHandler), it
	does not wait for one of its own published events to react to. What this hook actually does
	is bind the process-wide `agent_run_runner` to the collaborators it can only be given once
	the bus and the registry exist -- the same moment Knowledge Base's own runner is bound its
	publisher.

	Takes `instance_authorization_registry` in addition to the `registry`/`event_bus` pair other
	modules already take, since the runner's tools need it to authorize resource-level access
	exactly as the HTTP routes do. No shared interface fixes this signature across modules (root
	CLAUDE.md's event-driven-architecture note) -- this is a self-contained, opt-in addition.
	"""
	agent_run_runner.bind(
		event_publisher=InMemoryEventPublisher(event_bus),
		instance_authorization_registry=instance_authorization_registry,
	)


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""A conversation belongs to exactly one user, and so does the run it owns -- both policies
	are strictly self-only in v1, with no breadth-permission override (see ConversationAccessPolicy/
	AgentRunAccessPolicy's own docstrings)."""
	registry.register("conversation", ConversationAccessPolicy(_conversation_read_repository_scope))
	registry.register("agent_run", AgentRunAccessPolicy(_conversation_read_repository_scope))
