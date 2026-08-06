from __future__ import annotations

from app.modules.notifications.application.dto.notification_dto import NotificationDTO
from app.modules.notifications.application.mapping.action_serialization import deserialize_action, serialize_action
from app.modules.notifications.domain.entities.notification import Notification
from app.modules.notifications.infrastructure.persistence.models.notification_model import NotificationModel


def notification_to_model(notification: Notification) -> NotificationModel:
	return NotificationModel(
		id=notification.id,
		recipient_id=notification.recipient_id,
		title=notification.title,
		message=notification.message,
		type=notification.type,
		action=serialize_action(notification.action),
		notification_metadata=notification.metadata,
		created_at=notification.created_at,
		read_at=notification.read_at,
	)


def sync_notification_model(model: NotificationModel, notification: Notification) -> None:
	model.title = notification.title
	model.message = notification.message
	model.type = notification.type
	model.action = serialize_action(notification.action)
	model.notification_metadata = notification.metadata
	model.read_at = notification.read_at


def model_to_domain(model: NotificationModel) -> Notification:
	return Notification(
		id=model.id,
		recipient_id=model.recipient_id,
		title=model.title,
		message=model.message,
		type=model.type,
		action=deserialize_action(model.action),
		created_at=model.created_at,
		read_at=model.read_at,
		metadata=model.notification_metadata,
	)


def model_to_dto(model: NotificationModel) -> NotificationDTO:
	return NotificationDTO(
		id=model.id,
		recipient_id=model.recipient_id,
		title=model.title,
		message=model.message,
		type=model.type,
		action=deserialize_action(model.action),
		created_at=model.created_at,
		read_at=model.read_at,
		metadata=model.notification_metadata,
	)
