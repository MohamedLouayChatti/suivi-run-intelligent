from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any
from uuid import UUID

from app.modules.notifications.application.interfaces.notification_read_repository import NotificationReadRepository
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy

NotificationReadRepositoryScope = Callable[[], AbstractAsyncContextManager[NotificationReadRepository]]


def _parse_uuid(value: object) -> UUID | None:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(str(value))
	except (TypeError, ValueError):
		return None


class NotificationAccessPolicy(InstanceAuthorizationPolicy):
	"""Self-ownership only: a notification belongs to exactly one recipient, and
	only that recipient may read or mark it -- no admin override, matching how
	CommentAccessPolicy gates comment update/delete to the comment's own author."""

	def __init__(self, notification_repository_scope: NotificationReadRepositoryScope) -> None:
		self._notification_repository_scope = notification_repository_scope

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		notification_id = _parse_uuid(resource_id)
		if notification_id is None:
			return AuthorizationResult(False, "Invalid notification identifier.")

		if operation not in {"read", "mark_read"}:
			return AuthorizationResult(False, f"Unknown notification operation '{operation}'.")

		async with self._notification_repository_scope() as notifications:
			notification = await notifications.get_notification(notification_id)
		if notification is None:
			# Let the request through: the handler will raise the proper not-found
			# error. A missing resource is not an authorization outcome.
			return AuthorizationResult(True, "")
		if notification.recipient_id == current_user.id:
			return AuthorizationResult(True, "")
		return AuthorizationResult(False, "You can only access your own notifications.")
