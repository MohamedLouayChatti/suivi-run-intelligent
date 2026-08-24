from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from uuid import UUID

from app.modules.auth.domain.entities.permission import Permission
from app.modules.auth.domain.exceptions import CircularPermissionDependency


@dataclass(frozen=True, slots=True)
class PermissionDependencyGraph:
	"""The "a capability presupposes its reach" relation, as pure set algebra.

	A permission declares the ones it cannot be used without: `user.activate` needs
	`user.read_all`, because nothing else puts a user in front of the caller to activate.
	This holds the relation and answers questions about it; *who* may hold what is
	`AuthorizationService`'s to decide, since that spans the User and Role aggregates.

	Deliberately a value object rather than a service: it is derived reference data with no
	identity and no lifecycle, rebuilt from the permission catalog whenever it is needed.
	"""

	_direct: Mapping[UUID, frozenset[UUID]]

	@classmethod
	def from_permissions(cls, permissions: Iterable[Permission]) -> PermissionDependencyGraph:
		return cls({permission.id: frozenset(permission.required_permission_ids) for permission in permissions})

	def prerequisites_of(self, permission_id: UUID) -> frozenset[UUID]:
		"""Every permission `permission_id` transitively needs, itself excluded."""
		return frozenset(self._walk(permission_id, self._direct))

	def dependents_of(self, permission_id: UUID, *, within: Iterable[UUID]) -> frozenset[UUID]:
		"""Which of `within` would become unusable if `permission_id` were taken away.

		Restricted to a candidate set rather than answered over the whole catalog, because
		the callers are cascading revokes: what matters is what *this* role or user actually
		holds, not every permission that could theoretically depend on it.
		"""
		reverse = self._reverse()
		candidates = set(within)
		return frozenset(self._walk(permission_id, reverse) & candidates)

	def satisfied_subset(self, granted: Iterable[UUID]) -> set[UUID]:
		"""The largest subset of `granted` that is closed under this relation.

		The closure that makes an effective permission set coherent no matter how the stored
		data got that way -- a role reassigned out from under a direct grant, a revocation
		exception landing on something another permission needed.  Repeatedly drops whatever
		is missing a prerequisite until nothing more falls out, since dropping one permission
		can orphan another that required it.
		"""
		remaining = set(granted)
		while True:
			unsatisfied = {
				permission_id
				for permission_id in remaining
				if not self._direct.get(permission_id, frozenset()) <= remaining
			}
			if not unsatisfied:
				return remaining
			remaining -= unsatisfied

	def missing_prerequisites(self, permission_id: UUID, *, held: Iterable[UUID]) -> frozenset[UUID]:
		"""What `held` would still need before `permission_id` could be used."""
		return self.prerequisites_of(permission_id) - set(held)

	def _reverse(self) -> Mapping[UUID, frozenset[UUID]]:
		reverse: dict[UUID, set[UUID]] = {}
		for permission_id, required in self._direct.items():
			for prerequisite in required:
				reverse.setdefault(prerequisite, set()).add(permission_id)
		return {key: frozenset(value) for key, value in reverse.items()}

	@staticmethod
	def _walk(start: UUID, edges: Mapping[UUID, frozenset[UUID]]) -> set[UUID]:
		"""Transitive reach from `start`, excluding `start`, refusing to loop forever.

		A cycle is unreachable through the seeder, which refuses to synchronize one -- but a
		graph built from anything else would hang here rather than fail, so it is named.
		"""
		reached: set[UUID] = set()
		stack = [(start, (start,))]
		while stack:
			current, path = stack.pop()
			for neighbour in edges.get(current, frozenset()):
				if neighbour in path:
					raise CircularPermissionDependency()
				if neighbour in reached:
					continue
				reached.add(neighbour)
				stack.append((neighbour, path + (neighbour,)))
		return reached
