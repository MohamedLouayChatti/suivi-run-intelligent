from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class GenerateSimilarityResultsCommand:
	"""Mirrors the fields of TicketCreated this pipeline actually needs. Built by the
	infrastructure event handler from the event it receives.

	`description` is the raw, user-facing text. What gets embedded is derived from it by
	`preprocess_description`, never stored back onto the ticket.
	"""

	ticket_id: UUID
	description: str
	application: Application
	created_at: datetime
	genergy_id: str | None = None
	oceane_id: str | None = None
