from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application
from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class TicketsImportDiscarded(DomainEvent):
	"""A batch that had been imported was taken back out again, because the operation it belonged
	to could not be completed.

	Published as its own event rather than by suppressing the TicketsImported that preceded it: the
	import genuinely did happen and was genuinely undone, and an audit log that shows both is a
	record of what occurred. One that shows neither would quietly lose the fact that a thousand
	tickets appeared and disappeared.

	`reason` is the failure that triggered the compensation, carried so the log says why rather
	than only that.
	"""

	application: Application
	ticket_ids: tuple[UUID, ...]
	reason: str
