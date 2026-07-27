from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import SqlAlchemyUserReadRepository
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.security.attachment_access_policy import AttachmentAccessPolicy
from app.modules.ticket_management.application.security.comment_access_policy import CommentAccessPolicy
from app.modules.ticket_management.application.security.ticket_access_policy import TicketAccessPolicy
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import SqlAlchemyTicketReadRepository
from app.shared.database.session import create_session
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


def register_subscriptions(registry: SubscriptionRegistry) -> None:
	"""Register Ticket Management event consumers.

	Ticket Management currently only produces events, so it does not
	subscribe to any shared events yet. The function exists as the module's
	public bootstrap hook and will be extended when the module starts
	consuming events from other modules.
	"""
	return None


@asynccontextmanager
async def _ticket_read_repository_scope() -> AsyncIterator[TicketReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyTicketReadRepository(session)
	finally:
		await session.close()


@asynccontextmanager
async def _user_read_repository_scope() -> AsyncIterator[UserReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyUserReadRepository(session)
	finally:
		await session.close()


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Register Ticket Management's resource instance authorization policies."""
	registry.register("ticket", TicketAccessPolicy(_ticket_read_repository_scope, _user_read_repository_scope))
	registry.register("comment", CommentAccessPolicy(_ticket_read_repository_scope, _user_read_repository_scope))
	registry.register("attachment", AttachmentAccessPolicy(_ticket_read_repository_scope))
