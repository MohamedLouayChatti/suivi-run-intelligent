from __future__ import annotations

from app.shared.exceptions.domain_exceptions import DomainError


class TicketDomainError(DomainError):
	"""Base exception for ticket management domain errors."""


class InvalidStatusTransition(TicketDomainError):
	pass


class TransferDestinationRequired(TicketDomainError):
	pass


class TransferDestinationIsOrigin(TicketDomainError):
	pass


class OfferRequired(TicketDomainError):
	pass


class VersionRequired(TicketDomainError):
	pass


class ElementRequired(TicketDomainError):
	pass


class VioAppRequired(TicketDomainError):
	pass


class JiraIdRequired(TicketDomainError):
	pass


class ConditionalFieldForbidden(TicketDomainError):
	pass


class ResolutionNotesRequired(TicketDomainError):
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

class AssigneeUnchanged(TicketDomainError):
	pass

class AssigneeRequired(TicketDomainError):
	pass

class ChronologicalOrderViolation(TicketDomainError):
	pass
