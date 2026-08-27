from __future__ import annotations

from app.shared.exceptions.domain_exceptions import DomainError


class ConversationDomainError(DomainError):
	"""Base exception for conversational assistant domain errors."""


class EmptyMessageContent(ConversationDomainError):
	pass


class RunNotFound(ConversationDomainError):
	pass


class RunNotPending(ConversationDomainError):
	pass


class RunNotRunning(ConversationDomainError):
	pass


class InvalidToolInvocationOutcome(ConversationDomainError):
	pass
