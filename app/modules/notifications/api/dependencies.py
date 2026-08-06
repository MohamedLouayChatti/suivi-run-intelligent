from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.modules.notifications.application.interfaces.notification_publisher import NotificationPublisher
from app.modules.notifications.application.queries.count_unread_notifications.handler import CountUnreadNotificationsHandler
from app.modules.notifications.application.queries.list_notifications.handler import ListNotificationsHandler
from app.modules.notifications.application.services.notification_service import NotificationService
from app.modules.notifications.infrastructure.delivery.sse_connection_manager import connection_manager
from app.modules.notifications.infrastructure.delivery.sse_notification_publisher import SSENotificationPublisher
from app.modules.notifications.infrastructure.persistence.repositories.sqlalchemy_notification_read_repository import SqlAlchemyNotificationReadRepository
from app.modules.notifications.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.database.session import create_session


async def get_read_repository() -> AsyncIterator[SqlAlchemyNotificationReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyNotificationReadRepository(session)
	finally:
		await session.close()


def get_list_notifications_handler(
	repository: Annotated[SqlAlchemyNotificationReadRepository, Depends(get_read_repository)],
) -> ListNotificationsHandler:
	return ListNotificationsHandler(repository)


def get_count_unread_notifications_handler(
	repository: Annotated[SqlAlchemyNotificationReadRepository, Depends(get_read_repository)],
) -> CountUnreadNotificationsHandler:
	return CountUnreadNotificationsHandler(repository)


def get_notification_publisher() -> NotificationPublisher:
	return SSENotificationPublisher(connection_manager)


def get_notification_service(
	publisher: Annotated[NotificationPublisher, Depends(get_notification_publisher)],
) -> NotificationService:
	return NotificationService(SqlAlchemyUnitOfWork(), publisher)
