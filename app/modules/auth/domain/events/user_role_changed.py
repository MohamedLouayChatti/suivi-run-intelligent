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
	discarded_direct_permission_ids: frozenset[UUID]
	discarded_revoked_permission_ids: frozenset[UUID]
	"""The permission exceptions the role change swept away, on both sides.

	Setting a role replaces the user's whole permission profile, so any direct grant or
	revocation decided against the previous role goes with it.  Carried here because those
	exceptions were themselves administrative decisions, recorded in this log when they were
	made -- leaving their disappearance unrecorded would make the log say a user still holds a
	permission that was taken from them, with nothing in between to explain it.
	"""
