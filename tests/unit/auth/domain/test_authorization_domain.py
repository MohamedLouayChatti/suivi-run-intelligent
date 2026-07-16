from uuid import uuid4

import pytest

from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.events.permission_granted_to_user import PermissionGrantedToUser
from app.modules.auth.domain.events.permission_revoked_from_user import PermissionRevokedFromUser
from app.modules.auth.domain.events.user_created import UserCreated
from app.modules.auth.domain.exceptions import (
	InvalidPermissionState,
	PermissionAlreadyGranted,
	PermissionNotGranted,
)
from app.modules.auth.domain.services.authorization_service import AuthorizationService
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId


def make_user() -> User:
	return User.create(
		id=uuid4(),
		auth_provider_user_id=AuthProviderUserId("provider-user"),
		email="support@example.com",
		display_name="Support Engineer",
	)


def test_user_creation_records_event() -> None:
	user = make_user()

	events = user.pull_domain_events()

	assert user.active is True
	assert events == [
		UserCreated(
			user_id=user.id,
			auth_provider_user_id=user.auth_provider_user_id,
			email=user.email,
			display_name=user.display_name,
		)
	]
	assert user.pull_domain_events() == []


def test_user_permission_transitions_keep_sets_disjoint() -> None:
	user = make_user()
	user.pull_domain_events()
	permission_id = uuid4()

	user.revoke_permission(permission_id)
	user.grant_permission(permission_id)

	assert user.direct_permission_ids == {permission_id}
	assert user.revoked_permission_ids == set()
	assert user.pull_domain_events() == [
		PermissionRevokedFromUser(user_id=user.id, permission_id=permission_id),
		PermissionGrantedToUser(user_id=user.id, permission_id=permission_id)
	]


def test_user_rejects_overlapping_permission_state() -> None:
	permission_id = uuid4()

	with pytest.raises(InvalidPermissionState):
		User(
			id=uuid4(),
			auth_provider_user_id=AuthProviderUserId("provider-user"),
			email="support@example.com",
			display_name="Support Engineer",
			active=True,
			direct_permission_ids={permission_id},
			revoked_permission_ids={permission_id},
		)


def test_authorization_service_resolves_role_direct_and_revoked_permissions() -> None:
	user = make_user()
	role_permission_id = uuid4()
	direct_permission_id = uuid4()
	revoked_permission_id = uuid4()
	role = Role(id=uuid4(), name="support", permission_ids={role_permission_id, revoked_permission_id})
	user.assign_role(role.id)
	user.grant_permission(direct_permission_id)
	user.revoke_permission(revoked_permission_id)
	service = AuthorizationService()

	assert service.resolve_permissions(user, [role]) == {role_permission_id, direct_permission_id}
	assert service.has_permission(user, role_permission_id, [role]) is True
	with pytest.raises(PermissionAlreadyGranted):
		service.ensure_direct_permission_may_be_granted(user, role_permission_id, [role])
	with pytest.raises(PermissionNotGranted):
		service.ensure_direct_permission_may_be_revoked(user, revoked_permission_id, [role])
