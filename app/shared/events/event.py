from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
	"""Base envelope shared by every domain event: when it occurred, who caused it.

	Both fields are kw_only so inheriting them never affects a subclass's own field
	ordering -- Python's "no non-default field after a default field" dataclass rule is
	scoped to positional fields only, and kw_only fields sit in a separate keyword-only
	bucket regardless of default status. Subclasses keep declaring their own fields
	exactly as before; only event-construction call sites need `occurred_at=`/`actor_id=`
	as explicit keywords.

	actor_id is nullable: most events always carry a real one (threaded from
	current_user.id through the publishing command/handler/route), but the two events
	published from Auth's Clerk webhook flow (UserCreated, UserUpdated) have no
	authenticated CurrentUser to attribute -- see AuditEntryDTO.actor_label for how
	that's surfaced to API consumers.
	"""

	occurred_at: datetime
	actor_id: UUID | None = None
