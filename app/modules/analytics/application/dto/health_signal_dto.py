from __future__ import annotations

from dataclasses import dataclass

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class ApplicationHealthSignalDTO:
	"""The live numbers behind an application's health tier -- no `health` field, since tiering
	against a baseline is a domain decision made by the caller, not something the read side
	computes."""

	application: Application
	active_tickets: int
	avg_resolution_hours: float
	urgent_tickets: int
