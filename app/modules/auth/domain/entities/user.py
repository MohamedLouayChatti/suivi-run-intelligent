from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.domain.events.permission_granted_to_user import PermissionGrantedToUser
from app.modules.auth.domain.events.permission_revoked_from_user import PermissionRevokedFromUser
from app.modules.auth.domain.events.role_assigned_to_user import RoleAssignedToUser
from app.modules.auth.domain.events.role_revoked_from_user import RoleRevokedFromUser
from app.modules.auth.domain.events.user_activated import UserActivated
from app.modules.auth.domain.events.user_created import UserCreated
from app.modules.auth.domain.events.user_deactivated import UserDeactivated
from app.modules.auth.domain.exceptions import InvalidPermissionState
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.shared.events.event import DomainEvent


@dataclass
class User:
	"""Authorization aggregate that owns a user's role and permission exceptions."""

	id: UUID
	auth_provider_user_id: AuthProviderUserId
	email: str
	display_name: str
	active: bool
	role_ids: set[UUID] = field(default_factory=set)
	direct_permission_ids: set[UUID] = field(default_factory=set)
	revoked_permission_ids: set[UUID] = field(default_factory=set)

	def __post_init__(self) -> None:
		if self.direct_permission_ids & self.revoked_permission_ids:
			raise InvalidPermissionState()

	@classmethod
	def create(
		cls,
		*,
		id: UUID,
		auth_provider_user_id: AuthProviderUserId,
		email: str,
		display_name: str,
	) -> User:
		user = cls(
			id=id,
			auth_provider_user_id=auth_provider_user_id,
			email=email,
			display_name=display_name,
			active=True,
		)
		return user

	def assign_role(self, role_id: UUID) -> None:
		if role_id in self.role_ids:
			return
		self.role_ids.add(role_id)

	def revoke_role(self, role_id: UUID) -> None:
		if role_id not in self.role_ids:
			return
		self.role_ids.remove(role_id)

	def grant_permission(self, permission_id: UUID) -> None:
		self.revoked_permission_ids.discard(permission_id)
		self.direct_permission_ids.add(permission_id)

	def revoke_permission(self, permission_id: UUID) -> None:
		self.direct_permission_ids.discard(permission_id)
		self.revoked_permission_ids.add(permission_id)

	def activate(self) -> None:
		if self.active:
			return
		self.active = True

	def deactivate(self) -> None:
		if not self.active:
			return
		self.active = False