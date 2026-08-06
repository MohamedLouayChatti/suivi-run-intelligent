from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.notifications.api import dependencies as dep
from app.modules.notifications.api.schemas import MarkAllReadResponse, NotificationResponse, UnreadCountResponse
from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.queries.count_unread_notifications.query import CountUnreadNotificationsQuery
from app.modules.notifications.application.queries.list_notifications.query import ListNotificationsQuery
from app.modules.notifications.application.services.notification_service import NotificationService
from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.instance_permissions import require_instance_permission
from app.shared.security.permissions import require_permissions

now = lambda: datetime.now(UTC)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse], dependencies=[Depends(require_permissions("notification.read"))])
async def list_notifications(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_list_notifications_handler),
	unread_only: bool = False,
	page: Annotated[int, Query(ge=1)] = 1,
	page_size: Annotated[int, Query(ge=1, le=100)] = 100,
):
	query = ListNotificationsQuery(
		recipient_id=current_user.id, unread_only=unread_only,
		limit=page_size, offset=(page - 1) * page_size,
	)
	return [NotificationResponse.from_dto(notification) for notification in await handler.handle(query)]


@router.get("/unread-count", response_model=UnreadCountResponse, dependencies=[Depends(require_permissions("notification.read"))])
async def count_unread_notifications(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler=Depends(dep.get_count_unread_notifications_handler),
):
	count = await handler.handle(CountUnreadNotificationsQuery(recipient_id=current_user.id))
	return UnreadCountResponse(count=count)


@router.post(
	"/{notification_id}/read",
	response_model=NotificationResponse,
	dependencies=[
		Depends(require_permissions("notification.read")),
		Depends(require_instance_permission("notification", "mark_read", path_param="notification_id")),
	],
)
async def mark_notification_read(
	notification_id: UUID,
	service: Annotated[NotificationService, Depends(dep.get_notification_service)],
):
	notification = await service.mark_read(notification_id, now())
	return NotificationResponse.from_dto(NotificationDTO.from_notification(notification))


@router.post("/read-all", response_model=MarkAllReadResponse, dependencies=[Depends(require_permissions("notification.read"))])
async def mark_all_notifications_read(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	service: Annotated[NotificationService, Depends(dep.get_notification_service)],
):
	count = await service.mark_all_read(current_user.id, now())
	return MarkAllReadResponse(marked_read=count)
