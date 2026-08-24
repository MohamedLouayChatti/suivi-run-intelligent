from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.shared.events.event import DomainEvent


@dataclass(frozen=True)
class RolePermissionRevoked(DomainEvent):
	"""One or more permissions were taken away from a role in a single administrative act.

	Set-valued rather than one event per permission, because revoking a permission takes every
	permission depending on it along with it -- dropping `ticket.read` from a role removes the
	fifteen that cannot be used without it.  Those fifteen were not fifteen decisions; they
	were the consequence of one, and publishing them separately would write fifteen audit
	entries and page every member fifteen times for a single click.  The same reasoning that
	made `UserRoleChanged` one event rather than a revoked/assigned pair.

	`permission_ids` always contains the permission actually named by the caller; the rest, if
	any, are what depended on it.
	"""

	role_id: UUID
	permission_ids: frozenset[UUID]
