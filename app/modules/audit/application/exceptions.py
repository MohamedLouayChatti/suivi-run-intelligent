from __future__ import annotations

from app.shared.exceptions.application_exceptions import ApplicationError


class AuditApplicationError(ApplicationError):
	"""Base exception for audit application errors."""


class AuditEntryNotFound(AuditApplicationError):
	pass
