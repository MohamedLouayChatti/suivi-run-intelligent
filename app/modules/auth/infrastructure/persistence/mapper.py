from __future__ import annotations

from collections.abc import Iterable

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.domain.entities.permission import Permission
from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
from app.modules.auth.infrastructure.persistence.models.user_model import UserModel
from app.modules.auth.infrastructure.persistence.models.application_assignment_model import ApplicationAssignmentModel


def user_to_model(user: User, *, permissions: Iterable[PermissionModel] = ()) -> UserModel:
	model = UserModel(id=user.id, auth_provider_user_id=user.auth_provider_user_id.value, email=user.email, display_name=user.display_name, active=user.active, avatar_url=user.avatar_url, functional_team=user.functional_team, role_id=user.role_id)
	_sync_user_relationships(model, user, permissions)
	return model


def sync_user_model(model: UserModel, user: User, *, permissions: Iterable[PermissionModel] = ()) -> UserModel:
	model.auth_provider_user_id = user.auth_provider_user_id.value
	model.email = user.email
	model.display_name = user.display_name
	model.active = user.active
	model.avatar_url = user.avatar_url
	model.functional_team = user.functional_team
	model.role_id = user.role_id
	_sync_user_relationships(model, user, permissions)
	return model


def user_model_to_domain(model: UserModel) -> User:
	return User(id=model.id, auth_provider_user_id=AuthProviderUserId(model.auth_provider_user_id), email=model.email, display_name=model.display_name, active=model.active, role_id=model.role_id, avatar_url=model.avatar_url, functional_team=model.functional_team, application_assignments={ApplicationAssignment(x.application, x.assignment_type) for x in model.application_assignments}, direct_permission_ids={x.id for x in model.direct_permissions}, revoked_permission_ids={x.id for x in model.revoked_permissions})


def user_model_to_dto(model: UserModel) -> UserDTO:
	return UserDTO(id=model.id, auth_provider_user_id=AuthProviderUserId(model.auth_provider_user_id), email=model.email, display_name=model.display_name, active=model.active, role_id=model.role_id, avatar_url=model.avatar_url, functional_team=model.functional_team, application_assignments=frozenset(ApplicationAssignment(x.application, x.assignment_type) for x in model.application_assignments), direct_permission_ids={x.id for x in model.direct_permissions}, revoked_permission_ids={x.id for x in model.revoked_permissions})


def role_to_model(role: Role, *, permissions: Iterable[PermissionModel] = ()) -> RoleModel:
	model = RoleModel(id=role.id, name=role.name, requires_primary_application=role.requires_primary_application)
	model.permissions = list(permissions)
	return model


def sync_role_model(model: RoleModel, role: Role, *, permissions: Iterable[PermissionModel] = ()) -> RoleModel:
	model.name = role.name
	model.requires_primary_application = role.requires_primary_application
	model.permissions = list(permissions)
	return model


def role_model_to_domain(model: RoleModel) -> Role:
	return Role(id=model.id, name=model.name, permission_ids={x.id for x in model.permissions}, requires_primary_application=model.requires_primary_application)


def role_model_to_dto(model: RoleModel) -> RoleDTO:
	return RoleDTO(id=model.id, name=model.name, permission_ids={x.id for x in model.permissions}, requires_primary_application=model.requires_primary_application)


def permission_to_model(permission: Permission) -> PermissionModel:
	return PermissionModel(id=permission.id, name=permission.name, description=permission.description)


def permission_model_to_domain(model: PermissionModel) -> Permission:
	return Permission(id=model.id, name=model.name, description=model.description)


def permission_model_to_dto(model: PermissionModel) -> PermissionDTO:
	return PermissionDTO(id=model.id, name=model.name, description=model.description)


def _sync_user_relationships(model: UserModel, user: User, permissions: Iterable[PermissionModel]) -> None:
	permission_by_id = {permission.id: permission for permission in permissions}
	model.direct_permissions = [permission_by_id[x] for x in user.direct_permission_ids if x in permission_by_id]
	model.revoked_permissions = [permission_by_id[x] for x in user.revoked_permission_ids if x in permission_by_id]
	model.application_assignments = [
		ApplicationAssignmentModel(application=assignment.application, assignment_type=assignment.assignment_type)
		for assignment in user.application_assignments
	]
