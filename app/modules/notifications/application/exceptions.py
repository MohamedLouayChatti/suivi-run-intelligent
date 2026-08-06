from __future__ import annotations

from app.shared.exceptions.application_exceptions import ApplicationError


class NotificationApplicationError(ApplicationError):
	"""Base exception for notification application errors."""


class NotificationNotFound(NotificationApplicationError):
	pass
