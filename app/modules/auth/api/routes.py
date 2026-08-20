from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, status

from app.modules.auth.api.dependencies import (
	get_activate_user_handler, get_create_role_handler,
	get_create_user_handler, get_current_user_profile_handler, get_deactivate_user_handler,
	get_grant_permission_to_role_handler, get_grant_permission_to_user_handler,
	get_list_permissions_handler, get_list_roles_handler, get_list_users_handler,
	get_permission_handler, get_revoke_permission_from_role_handler,
	get_revoke_permission_from_user_handler, get_role_handler,
	get_role_permissions_handler, get_set_user_organizational_identity_handler,
	get_set_user_role_handler, get_update_user_handler,
	get_user_direct_permissions_handler, get_user_handler, get_user_role_handler,
	get_user_revoked_permissions_handler,
)
from app.modules.auth.api.schemas import MeResponse, PermissionResponse, RoleCreateRequest, RoleResponse, UserCreateRequest, UserDirectoryResponse, UserOrganizationalIdentityRequest, UserResponse, UserUpdateRequest
from app.modules.auth.application.commands.activate_user.handler import ActivateUserHandler
from app.modules.auth.application.commands.set_user_role.handler import SetUserRoleHandler
from app.modules.auth.application.commands.set_user_organizational_identity.handler import SetUserOrganizationalIdentityHandler
from app.modules.auth.application.commands.create_role.handler import CreateRoleHandler
from app.modules.auth.application.commands.create_user.handler import CreateUserHandler
from app.modules.auth.application.commands.deactivate_user.handler import DeactivateUserHandler
from app.modules.auth.application.commands.grant_permission_to_role.handler import GrantPermissionToRoleHandler
from app.modules.auth.application.commands.grant_permission_to_user.handler import GrantPermissionToUserHandler
from app.modules.auth.application.commands.revoke_permission_from_role.handler import RevokePermissionFromRoleHandler
from app.modules.auth.application.commands.revoke_permission_from_user.handler import RevokePermissionFromUserHandler
from app.modules.auth.application.commands.update_user.handler import UpdateUserHandler
from app.modules.auth.application.queries.get_current_user_profile.handler import GetCurrentUserProfileHandler
from app.modules.auth.application.queries.get_permission.handler import GetPermissionHandler
from app.modules.auth.application.queries.get_role.handler import GetRoleHandler
from app.modules.auth.application.queries.get_role_permissions.handler import GetRolePermissionsHandler
from app.modules.auth.application.queries.get_user.handler import GetUserHandler
from app.modules.auth.application.queries.get_user_direct_permissions.handler import GetUserDirectPermissionsHandler
from app.modules.auth.application.queries.get_user_revoked_permissions.handler import GetUserRevokedPermissionsHandler
from app.modules.auth.application.queries.get_user_role.handler import GetUserRoleHandler
from app.modules.auth.application.queries.list_permissions.handler import ListPermissionsHandler
from app.modules.auth.application.queries.list_roles.handler import ListRolesHandler
from app.modules.auth.application.queries.list_users.handler import ListUsersHandler
from app.modules.auth.application.commands.activate_user.command import ActivateUserCommand
from app.modules.auth.application.commands.set_user_role.command import SetUserRoleCommand
from app.modules.auth.application.commands.set_user_organizational_identity.command import SetUserOrganizationalIdentityCommand
from app.modules.auth.application.commands.create_role.command import CreateRoleCommand
from app.modules.auth.application.commands.create_user.command import CreateUserCommand
from app.modules.auth.application.commands.deactivate_user.command import DeactivateUserCommand
from app.modules.auth.application.commands.grant_permission_to_role.command import GrantPermissionToRoleCommand
from app.modules.auth.application.commands.grant_permission_to_user.command import GrantPermissionToUserCommand
from app.modules.auth.application.commands.revoke_permission_from_role.command import RevokePermissionFromRoleCommand
from app.modules.auth.application.commands.revoke_permission_from_user.command import RevokePermissionFromUserCommand
from app.modules.auth.application.commands.update_user.command import UpdateUserCommand
from app.modules.auth.application.queries.get_current_user_profile.query import GetCurrentUserProfileQuery
from app.modules.auth.application.queries.get_permission.query import GetPermissionQuery
from app.modules.auth.application.queries.get_role.query import GetRoleQuery
from app.modules.auth.application.queries.get_role_permissions.query import GetRolePermissionsQuery
from app.modules.auth.application.queries.get_user.query import GetUserQuery
from app.modules.auth.application.queries.get_user_direct_permissions.query import GetUserDirectPermissionsQuery
from app.modules.auth.application.queries.get_user_revoked_permissions.query import GetUserRevokedPermissionsQuery
from app.modules.auth.application.queries.get_user_role.query import GetUserRoleQuery
from app.modules.auth.application.queries.list_permissions.query import ListPermissionsQuery
from app.modules.auth.application.queries.list_roles.query import ListRolesQuery
from app.modules.auth.application.queries.list_users.query import ListUsersQuery
from app.modules.auth.domain.value_objects.auth_provider_user_id import AuthProviderUserId

from app.shared.security.current_user import CurrentUser, get_current_user
from app.shared.security.instance_permissions import require_instance_permission
from app.shared.security.permissions import require_permissions

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/me", response_model=MeResponse)
async def get_me(
	current_user: Annotated[CurrentUser, Depends(get_current_user)],
	handler: Annotated[GetCurrentUserProfileHandler, Depends(get_current_user_profile_handler)],
) -> MeResponse:
	return MeResponse.from_dto(await handler.handle(GetCurrentUserProfileQuery(user_id=current_user.id)))


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_permissions("user.read_all"))])
async def list_users(handler: Annotated[ListUsersHandler, Depends(get_list_users_handler)], page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 100) -> list[UserResponse]:
	return [UserResponse.from_dto(user) for user in await handler.handle(ListUsersQuery(limit=page_size, offset=(page - 1) * page_size))]


@router.get("/users/directory", response_model=list[UserDirectoryResponse], dependencies=[Depends(require_permissions("user.read"))])
async def list_user_directory(handler: Annotated[ListUsersHandler, Depends(get_list_users_handler)], page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 100) -> list[UserDirectoryResponse]:
	return [UserDirectoryResponse.from_dto(user) for user in await handler.handle(ListUsersQuery(limit=page_size, offset=(page - 1) * page_size))]


@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permissions("user.read")), Depends(require_instance_permission("user", "read", path_param="user_id"))])
async def get_user(user_id: UUID, handler: Annotated[GetUserHandler, Depends(get_user_handler)]) -> UserResponse:
	return UserResponse.from_dto(await handler.handle(GetUserQuery(user_id=user_id)))


@router.post("/users/{user_id}/activate", response_model=UserResponse, dependencies=[Depends(require_permissions("user.activate"))])
async def activate_user(user_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[ActivateUserHandler, Depends(get_activate_user_handler)]) -> UserResponse:
	return UserResponse.from_dto(await handler.handle(ActivateUserCommand(user_id=user_id, actor_id=current_user.id)))


@router.post("/users/{user_id}/deactivate", response_model=UserResponse, dependencies=[Depends(require_permissions("user.deactivate")), Depends(require_instance_permission("user", "deactivate", path_param="user_id"))])
async def deactivate_user(user_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[DeactivateUserHandler, Depends(get_deactivate_user_handler)]) -> UserResponse:
	return UserResponse.from_dto(await handler.handle(DeactivateUserCommand(user_id=user_id, actor_id=current_user.id)))


@router.get("/users/{user_id}/role", response_model=RoleResponse, dependencies=[Depends(require_permissions("user.read")), Depends(require_instance_permission("user", "read_role", path_param="user_id"))])
async def get_user_role(user_id: UUID, handler: Annotated[GetUserRoleHandler, Depends(get_user_role_handler)]) -> RoleResponse:
	return RoleResponse.from_dto(await handler.handle(GetUserRoleQuery(user_id=user_id)))


@router.get("/users/{user_id}/permissions", response_model=list[PermissionResponse], dependencies=[Depends(require_permissions("user.read")), Depends(require_instance_permission("user", "read_permissions", path_param="user_id"))])
async def get_user_direct_permissions(user_id: UUID, handler: Annotated[GetUserDirectPermissionsHandler, Depends(get_user_direct_permissions_handler)]) -> list[PermissionResponse]:
	return [PermissionResponse.from_dto(permission) for permission in await handler.handle(GetUserDirectPermissionsQuery(user_id=user_id))]


@router.get("/users/{user_id}/revoked-permissions", response_model=list[PermissionResponse], dependencies=[Depends(require_permissions("user.read")), Depends(require_instance_permission("user", "read_revoked_permissions", path_param="user_id"))])
async def get_user_revoked_permissions(user_id: UUID, handler: Annotated[GetUserRevokedPermissionsHandler, Depends(get_user_revoked_permissions_handler)]) -> list[PermissionResponse]:
	return [PermissionResponse.from_dto(permission) for permission in await handler.handle(GetUserRevokedPermissionsQuery(user_id=user_id))]


@router.put("/users/{user_id}/role/{role_id}", response_model=UserResponse, dependencies=[Depends(require_permissions("role.assign")), Depends(require_instance_permission("user", "set_role", path_param="user_id"))])
async def set_user_role(user_id: UUID, role_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[SetUserRoleHandler, Depends(get_set_user_role_handler)]) -> UserResponse:
	return UserResponse.from_dto(await handler.handle(SetUserRoleCommand(user_id=user_id, role_id=role_id, actor_id=current_user.id)))


@router.put("/users/{user_id}/organizational-identity", response_model=UserResponse, dependencies=[Depends(require_permissions("user.manage_organization")), Depends(require_instance_permission("user", "set_organizational_identity", path_param="user_id"))])
async def set_user_organizational_identity(user_id: UUID, request: UserOrganizationalIdentityRequest, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[SetUserOrganizationalIdentityHandler, Depends(get_set_user_organizational_identity_handler)]) -> UserResponse:
	return UserResponse.from_dto(await handler.handle(SetUserOrganizationalIdentityCommand(user_id=user_id, functional_team=request.functional_team, application_assignments=frozenset(assignment.to_value_object() for assignment in request.application_assignments), actor_id=current_user.id)))


@router.post("/users/{user_id}/permissions/{permission_id}", response_model=UserResponse, dependencies=[Depends(require_permissions("permission.grant_to_user"))])
async def grant_permission_to_user(user_id: UUID, permission_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[GrantPermissionToUserHandler, Depends(get_grant_permission_to_user_handler)]) -> UserResponse:
	return UserResponse.from_dto(await handler.handle(GrantPermissionToUserCommand(user_id=user_id, permission_id=permission_id, actor_id=current_user.id)))


@router.delete("/users/{user_id}/permissions/{permission_id}", response_model=UserResponse, dependencies=[Depends(require_permissions("permission.revoke_from_user")), Depends(require_instance_permission("user", "revoke_permission", path_param="user_id"))])
async def revoke_permission_from_user(user_id: UUID, permission_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[RevokePermissionFromUserHandler, Depends(get_revoke_permission_from_user_handler)]) -> UserResponse:
	return UserResponse.from_dto(await handler.handle(RevokePermissionFromUserCommand(user_id=user_id, permission_id=permission_id, actor_id=current_user.id)))


@router.get("/roles", response_model=list[RoleResponse], dependencies=[Depends(require_permissions("role.read_all"))])
async def list_roles(handler: Annotated[ListRolesHandler, Depends(get_list_roles_handler)], page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 100) -> list[RoleResponse]:
	return [RoleResponse.from_dto(role) for role in await handler.handle(ListRolesQuery(limit=page_size, offset=(page - 1) * page_size))]


@router.get("/roles/{role_id}", response_model=RoleResponse, dependencies=[Depends(require_permissions("role.read")), Depends(require_instance_permission("role", "read", path_param="role_id"))])
async def get_role(role_id: UUID, handler: Annotated[GetRoleHandler, Depends(get_role_handler)]) -> RoleResponse:
	return RoleResponse.from_dto(await handler.handle(GetRoleQuery(role_id=role_id)))


@router.get("/roles/{role_id}/permissions", response_model=list[PermissionResponse], dependencies=[Depends(require_permissions("role.read")), Depends(require_instance_permission("role", "read_permissions", path_param="role_id"))])
async def get_role_permissions(role_id: UUID, handler: Annotated[GetRolePermissionsHandler, Depends(get_role_permissions_handler)]) -> list[PermissionResponse]:
	return [PermissionResponse.from_dto(permission) for permission in await handler.handle(GetRolePermissionsQuery(role_id=role_id))]


@router.post("/roles/{role_id}/permissions/{permission_id}", response_model=RoleResponse, dependencies=[Depends(require_permissions("permission.grant_to_role"))])
async def grant_permission_to_role(role_id: UUID, permission_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[GrantPermissionToRoleHandler, Depends(get_grant_permission_to_role_handler)]) -> RoleResponse:
	return RoleResponse.from_dto(await handler.handle(GrantPermissionToRoleCommand(role_id=role_id, permission_id=permission_id, actor_id=current_user.id)))


@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=RoleResponse, dependencies=[Depends(require_permissions("permission.revoke_from_role"))])
async def revoke_permission_from_role(role_id: UUID, permission_id: UUID, current_user: Annotated[CurrentUser, Depends(get_current_user)], handler: Annotated[RevokePermissionFromRoleHandler, Depends(get_revoke_permission_from_role_handler)]) -> RoleResponse:
	return RoleResponse.from_dto(await handler.handle(RevokePermissionFromRoleCommand(role_id=role_id, permission_id=permission_id, actor_id=current_user.id)))


@router.get("/permissions", response_model=list[PermissionResponse], dependencies=[Depends(require_permissions("permission.read"))])
async def list_permissions(handler: Annotated[ListPermissionsHandler, Depends(get_list_permissions_handler)], page: Annotated[int, Query(ge=1)] = 1, page_size: Annotated[int, Query(ge=1, le=100)] = 100) -> list[PermissionResponse]:
	return [PermissionResponse.from_dto(permission) for permission in await handler.handle(ListPermissionsQuery(limit=page_size, offset=(page - 1) * page_size))]


@router.get("/permissions/{permission_id}", response_model=PermissionResponse, dependencies=[Depends(require_permissions("permission.read"))])
async def get_permission(permission_id: UUID, handler: Annotated[GetPermissionHandler, Depends(get_permission_handler)]) -> PermissionResponse:
	return PermissionResponse.from_dto(await handler.handle(GetPermissionQuery(permission_id=permission_id)))
