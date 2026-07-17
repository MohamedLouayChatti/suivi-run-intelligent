
from __future__ import annotations

from collections.abc import Iterable

from app.modules.auth.application.dto.permission_dto import PermissionDTO
from app.modules.auth.application.dto.role_dto import RoleDTO
from app.modules.auth.application.dto.user_dto import UserDTO
from app.modules.auth.domain.entities.permission import Permission
from app.modules.auth.domain.entities.role import Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId
from app.modules.auth.infrastructure.persistence.models.permission_model import PermissionModel
from app.modules.auth.infrastructure.persistence.models.role_model import RoleModel
from app.modules.auth.infrastructure.persistence.models.user_model import UserModel


def user_to_model(user: User, *, roles: Iterable[RoleModel] = (), permissions: Iterable[PermissionModel] = ()) -> UserModel:
	model = UserModel(id=user.id, auth_provider_user_id=user.auth_provider_user_id.value, email=user.email, display_name=user.display_name, active=user.active)
	_sync_user_relationships(model, user, roles, permissions)
	return model


def sync_user_model(model: UserModel, user: User, *, roles: Iterable[RoleModel] = (), permissions: Iterable[PermissionModel] = ()) -> UserModel:
	model.auth_provider_user_id = user.auth_provider_user_id.value
	model.email = user.email
	model.display_name = user.display_name
	model.active = user.active
	_sync_user_relationships(model, user, roles, permissions)
	return model


def user_model_to_domain(model: UserModel) -> User:
	return User(id=model.id, auth_provider_user_id=AuthProviderUserId(model.auth_provider_user_id), email=model.email, display_name=model.display_name, active=model.active, role_ids={x.id for x in model.roles}, direct_permission_ids={x.id for x in model.direct_permissions}, revoked_permission_ids={x.id for x in model.revoked_permissions})


def user_model_to_dto(model: UserModel) -> UserDTO:
	return UserDTO(id=model.id, auth_provider_user_id=AuthProviderUserId(model.auth_provider_user_id), email=model.email, display_name=model.display_name, active=model.active, role_ids={x.id for x in model.roles}, direct_permission_ids={x.id for x in model.direct_permissions}, revoked_permission_ids={x.id for x in model.revoked_permissions})


def role_to_model(role: Role, *, permissions: Iterable[PermissionModel] = ()) -> RoleModel:
	model = RoleModel(id=role.id, name=role.name)
	model.permissions = list(permissions)
	return model


def sync_role_model(model: RoleModel, role: Role, *, permissions: Iterable[PermissionModel] = ()) -> RoleModel:
	model.name = role.name
	model.permissions = list(permissions)
	return model


def role_model_to_domain(model: RoleModel) -> Role:
	return Role(id=model.id, name=model.name, permission_ids={x.id for x in model.permissions})


def role_model_to_dto(model: RoleModel) -> RoleDTO:
	return RoleDTO(id=model.id, name=model.name, permission_ids={x.id for x in model.permissions})


def permission_to_model(permission: Permission) -> PermissionModel:
	return PermissionModel(id=permission.id, name=permission.name, description=permission.description)


def permission_model_to_domain(model: PermissionModel) -> Permission:
	return Permission(id=model.id, name=model.name, description=model.description)


def permission_model_to_dto(model: PermissionModel) -> PermissionDTO:
	return PermissionDTO(id=model.id, name=model.name, description=model.description)


def _sync_user_relationships(model: UserModel, user: User, roles: Iterable[RoleModel], permissions: Iterable[PermissionModel]) -> None:
	permission_by_id = {permission.id: permission for permission in permissions}
	model.roles = [role for role in roles if role.id in user.role_ids]
	model.direct_permissions = [permission_by_id[x] for x in user.direct_permission_ids if x in permission_by_id]
	model.revoked_permissions = [permission_by_id[x] for x in user.revoked_permission_ids if x in permission_by_id]
