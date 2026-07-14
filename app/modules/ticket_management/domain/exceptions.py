from __future__ import annotations

from app.shared.exceptions.exceptions import DomainError


class TicketDomainError(DomainError):
	"""Base exception for ticket management domain errors."""


class InvalidStatusTransition(TicketDomainError):
	pass


class PendingReasonRequired(TicketDomainError):
	pass


class ResolutionNotesRequired(TicketDomainError):
	pass


class TicketAlreadyAssigned(TicketDomainError):
	pass


class TicketNotAssigned(TicketDomainError):
	pass


class TicketClosed(TicketDomainError):
	pass

class TicketArchived(TicketDomainError):
	pass

class TicketNotArchived(TicketDomainError):
	pass

class CommentNotFound(TicketDomainError):
	pass


class AttachmentNotFound(TicketDomainError):
	pass

class CommentDeleted(TicketDomainError):
	pass

class AttachmentDeleted(TicketDomainError):
	pass

class DuplicateAttachment(TicketDomainError):
	pass


class EmptyComment(TicketDomainError):
	pass


class EmptyTitle(TicketDomainError):
	pass


class EmptyDescription(TicketDomainError):
	pass


class InvalidAssignee(TicketDomainError):
	pass

class SameApplicationTransfer(TicketDomainError):
	pass