from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class PermissionRevokedFromUser(DomainEvent):
	"""One or more permissions were taken away from a single user in one administrative act.

	Set-valued for the same reason as `RolePermissionRevoked`: a revocation carries away
	everything that depended on the permission revoked, and those dependents are the
	consequence of one decision rather than decisions of their own.
	"""

	user_id: UUID
	permission_ids: frozenset[UUID]
