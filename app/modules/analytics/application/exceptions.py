from __future__ import annotations

from app.modules.ticket_management.domain.enums.application import Application
from app.shared.exceptions.application_exceptions import ApplicationError


class AnalyticsApplicationError(ApplicationError):
	"""Base exception for Analytics application errors."""


class UnsupportedInsightsApplication(AnalyticsApplicationError):
	"""Raised when application insights are requested for an application that has no
	dedicated widget (FCI has none; "all" is not a single application)."""

	def __init__(self, application: Application) -> None:
		super().__init__(f"No application insights are defined for '{application.value}'.")
