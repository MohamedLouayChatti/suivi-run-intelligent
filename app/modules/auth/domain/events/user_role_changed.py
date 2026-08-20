from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class UserRoleChanged(DomainEvent):
	"""A user's one role was replaced by another.

	One event rather than the revoked/assigned pair this replaced: a user always holds exactly
	one role, so there is no moment at which the old one is gone and the new one has not
	arrived.  Splitting it in two would have written that non-existent moment into the audit
	log and paged the user twice for a single administrative act.
	"""

	user_id: UUID
	previous_role_id: UUID
	new_role_id: UUID
