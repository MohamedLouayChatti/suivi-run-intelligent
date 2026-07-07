from __future__ import annotations


class TicketApplicationError(Exception):
	"""Base exception for ticket management application errors."""


class TicketNotFound(TicketApplicationError):
	pass


class CommentNotFound(TicketApplicationError):
	pass


class AttachmentNotFound(TicketApplicationError):
	pass
