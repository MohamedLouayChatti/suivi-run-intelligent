from __future__ import annotations

from app.shared.exceptions.application_exceptions import ApplicationError


class ConversationApplicationError(ApplicationError):
	"""Base exception for conversational assistant application errors."""


class ConversationNotFound(ConversationApplicationError):
	pass
