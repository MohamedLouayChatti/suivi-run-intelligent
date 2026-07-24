from __future__ import annotations

from app.shared.exceptions.application_exceptions import ApplicationError

class TicketApplicationError(ApplicationError):
	"""Base exception for ticket management application errors."""


class TicketNotFound(TicketApplicationError):
	pass


class CommentNotFound(TicketApplicationError):
	pass


class AttachmentNotFound(TicketApplicationError):
	pass


class AssigneeNotFound(TicketApplicationError):
	pass


class AssigneeNotAuthorized(TicketApplicationError):
	pass
