from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class Permission:
	"""Reference-data entity representing an authorization capability."""

	id: UUID
	name: str
	description: str
	required_permission_ids: frozenset[UUID] = field(default_factory=frozenset)
	"""The permissions that must be held for this one to be usable at all.

	Direct prerequisites only -- the transitive reach is computed by
	`PermissionDependencyGraph`, so a permission never restates what its own prerequisites
	already require.  Reference data like the rest of this entity: seeded from the catalog,
	never edited at runtime.
	"""
