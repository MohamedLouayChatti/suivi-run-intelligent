from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.modules.auth.application.interfaces.permission_read_repository import PermissionReadRepository
from app.modules.auth.application.interfaces.role_read_repository import RoleReadRepository
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_permission_read_repository import SqlAlchemyPermissionReadRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_role_read_repository import SqlAlchemyRoleReadRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import SqlAlchemyUserReadRepository
from app.modules.notifications.application.interfaces.notification_publisher import NotificationPublisher
from app.modules.notifications.application.mapping.notification_mapper import NotificationMapper
from app.modules.notifications.application.mapping.recipient_resolution import RecipientResolver
from app.modules.notifications.application.security.notification_access_policy import NotificationAccessPolicy
from app.modules.notifications.infrastructure.delivery.sse_connection_manager import connection_manager
from app.modules.notifications.infrastructure.delivery.sse_notification_publisher import SSENotificationPublisher
from app.modules.notifications.infrastructure.events.handlers.notification_event_handler import NotificationEventHandler
from app.modules.notifications.infrastructure.persistence.repositories.sqlalchemy_notification_read_repository import SqlAlchemyNotificationReadRepository
from app.modules.notifications.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import SqlAlchemyTicketReadRepository
from app.shared.database.session import create_session
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry

from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded
from app.modules.ticket_management.domain.events.attachment_deleted import AttachmentDeleted
from app.modules.ticket_management.domain.events.comment_added import CommentAdded
from app.modules.ticket_management.domain.events.comment_deleted import CommentDeleted
from app.modules.ticket_management.domain.events.comment_edited import CommentEdited
from app.modules.ticket_management.domain.events.priority_changed import PriorityChanged
from app.modules.ticket_management.domain.events.ticket_archived import TicketArchived
from app.modules.ticket_management.domain.events.ticket_reassigned import TicketReassigned
from app.modules.ticket_management.domain.events.ticket_restored import TicketRestored
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.modules.ticket_management.domain.events.ticket_transferred import TicketTransferred

from app.modules.auth.domain.events.permission_granted_to_user import PermissionGrantedToUser
from app.modules.auth.domain.events.permission_revoked_from_user import PermissionRevokedFromUser
from app.modules.auth.domain.events.role_assigned_to_user import RoleAssignedToUser
from app.modules.auth.domain.events.role_permission_granted import RolePermissionGranted
from app.modules.auth.domain.events.role_permission_revoked import RolePermissionRevoked
from app.modules.auth.domain.events.role_revoked_from_user import RoleRevokedFromUser
from app.modules.auth.domain.events.user_activated import UserActivated
from app.modules.auth.domain.events.user_created import UserCreated
from app.modules.auth.domain.events.user_deactivated import UserDeactivated

NOTIFIED_EVENT_TYPES = (
	TicketReassigned, PriorityChanged, TicketStatusChanged, CommentAdded, CommentEdited, CommentDeleted,
	AttachmentAdded, AttachmentDeleted, TicketArchived, TicketRestored, TicketTransferred,
	UserActivated, UserDeactivated, RoleAssignedToUser, RoleRevokedFromUser,
	PermissionGrantedToUser, PermissionRevokedFromUser, RolePermissionGranted, RolePermissionRevoked, UserCreated,
)


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


@asynccontextmanager
async def _role_read_repository_scope() -> AsyncIterator[RoleReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyRoleReadRepository(session)
	finally:
		await session.close()


@asynccontextmanager
async def _permission_read_repository_scope() -> AsyncIterator[PermissionReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyPermissionReadRepository(session)
	finally:
		await session.close()


@asynccontextmanager
async def _notification_read_repository_scope() -> AsyncIterator[SqlAlchemyNotificationReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyNotificationReadRepository(session)
	finally:
		await session.close()


def register_subscriptions(registry: SubscriptionRegistry) -> None:
	"""Subscribe Notifications' single generic handler to every notified domain
	event type -- same shape as Audit's register_subscriptions. The cross-module
	scope factories built here (Ticket Management's TicketReadRepository, Auth's
	UserReadRepository/RoleReadRepository) mirror the exact precedent already in
	Audit's own api/dependencies.py, which imports Auth's SqlAlchemyUserReadRepository
	directly for the same reason: composition-root/wiring code is where this
	codebase already reaches into a foreign module's concrete Infrastructure class
	to construct a session-scoped read repository.
	"""
	recipients = RecipientResolver(
		_ticket_read_repository_scope, _user_read_repository_scope,
		_role_read_repository_scope, _permission_read_repository_scope,
	)
	mapper = NotificationMapper(recipients)
	publisher: NotificationPublisher = SSENotificationPublisher(connection_manager)
	handler = NotificationEventHandler(SqlAlchemyUnitOfWork, mapper, publisher)
	for event_type in NOTIFIED_EVENT_TYPES:
		registry.subscribe(event_type, handler)


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Register Notifications' own resource instance authorization policy: a
	notification belongs to exactly one recipient."""
	registry.register("notification", NotificationAccessPolicy(_notification_read_repository_scope))
