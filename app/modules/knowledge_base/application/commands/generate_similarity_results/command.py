from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class GenerateSimilarityResultsCommand:
	"""Mirrors the fields of TicketCreated this pipeline actually needs. Built by the
	infrastructure event handler from the event it receives"""

	ticket_id: UUID
	description: str
	application: Application
	created_at: datetime
