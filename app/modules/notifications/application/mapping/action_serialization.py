from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import UUID

from app.modules.notifications.domain.value_objects.notification_action import (
	NotificationAction,
	OpenCommentAction,
	OpenTicketAction,
	OpenUserAction,
)

# JSONB dict with a "type" discriminator, mirroring audit_entries.payload. Lives in
# Application (not Infrastructure) because both the Infrastructure persistence
# mapper (JSONB column) and the API response schema need the exact same JSON
# shape -- defining it once here keeps both in sync instead of duplicating it.
_ACTION_SERIALIZERS: dict[type[NotificationAction], Callable[[NotificationAction], dict[str, Any]]] = {
	OpenTicketAction: lambda action: {"type": "open_ticket", "ticket_id": str(action.ticket_id)},
	OpenCommentAction: lambda action: {"type": "open_comment", "ticket_id": str(action.ticket_id), "comment_id": str(action.comment_id)},
	OpenUserAction: lambda action: {"type": "open_user", "user_id": str(action.user_id)},
}

_ACTION_DESERIALIZERS: dict[str, Callable[[dict[str, Any]], NotificationAction]] = {
	"open_ticket": lambda data: OpenTicketAction(UUID(data["ticket_id"])),
	"open_comment": lambda data: OpenCommentAction(UUID(data["ticket_id"]), UUID(data["comment_id"])),
	"open_user": lambda data: OpenUserAction(UUID(data["user_id"])),
}


def serialize_action(action: NotificationAction | None) -> dict[str, Any] | None:
	if action is None:
		return None
	serializer = _ACTION_SERIALIZERS.get(type(action))
	if serializer is None:
		raise ValueError(f"No serializer registered for action type {type(action).__name__}")
	return serializer(action)


def deserialize_action(data: dict[str, Any] | None) -> NotificationAction | None:
	if data is None:
		return None
	deserializer = _ACTION_DESERIALIZERS.get(data["type"])
	if deserializer is None:
		raise ValueError(f"No deserializer registered for action discriminator {data['type']!r}")
	return deserializer(data)
