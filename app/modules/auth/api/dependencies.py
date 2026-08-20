from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from typing import Any

from app.modules.auth.application.commands.activate_user.handler import ActivateUserHandler
from app.modules.auth.application.commands.set_user_role.handler import SetUserRoleHandler
from app.modules.auth.application.commands.create_role.handler import CreateRoleHandler
from app.modules.auth.application.commands.create_user.handler import CreateUserHandler
from app.modules.auth.application.commands.deactivate_user.handler import DeactivateUserHandler
from app.modules.auth.application.commands.grant_permission_to_role.handler import GrantPermissionToRoleHandler
from app.modules.auth.application.commands.grant_permission_to_user.handler import GrantPermissionToUserHandler
from app.modules.auth.application.commands.revoke_permission_from_role.handler import RevokePermissionFromRoleHandler
from app.modules.auth.application.commands.revoke_permission_from_user.handler import RevokePermissionFromUserHandler
from app.modules.auth.application.commands.update_user.handler import UpdateUserHandler
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.queries.get_current_user_profile.handler import GetCurrentUserProfileHandler
from app.modules.auth.application.queries.get_effective_permissions.handler import GetEffectivePermissionsHandler
from app.modules.auth.application.queries.get_user.handler import GetUserHandler
from app.modules.auth.application.queries.get_user_role.handler import GetUserRoleHandler
from app.modules.auth.application.queries.get_user_direct_permissions.handler import GetUserDirectPermissionsHandler
from app.modules.auth.application.queries.get_user_revoked_permissions.handler import GetUserRevokedPermissionsHandler
from app.modules.auth.application.queries.get_role.handler import GetRoleHandler
from app.modules.auth.application.queries.get_role_permissions.handler import GetRolePermissionsHandler
from app.modules.auth.application.queries.get_permission.handler import GetPermissionHandler
from app.modules.auth.application.queries.list_users.handler import ListUsersHandler
from app.modules.auth.application.queries.list_roles.handler import ListRolesHandler
from app.modules.auth.application.queries.list_permissions.handler import ListPermissionsHandler
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_permission_read_repository import SqlAlchemyPermissionReadRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_role_read_repository import SqlAlchemyRoleReadRepository
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import SqlAlchemyUserReadRepository
from app.modules.auth.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.modules.auth.infrastructure.providers.clerk_jwt_verifier import ClerkJWTVerifier
from app.modules.auth.infrastructure.providers.clerk_webhook_verifier import ClerkWebhookVerifier
from app.modules.auth.domain.services.authorization_service import AuthorizationService
from app.shared.database.session import create_session
from app.shared.events.event_bus import InMemoryEventBus
from app.shared.events.event_publisher import EventPublisher
from app.modules.auth.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from app.shared.security.auth_provider import AuthProvider


async def get_unit_of_work() -> AsyncIterator[SqlAlchemyUnitOfWork]:
	uow = SqlAlchemyUnitOfWork()
	try:
		yield uow
	finally:
		await uow.close()


async def get_user_read_repository() -> AsyncIterator[SqlAlchemyUserReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyUserReadRepository(session)
	finally:
		await session.close()


async def get_role_read_repository() -> AsyncIterator[SqlAlchemyRoleReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyRoleReadRepository(session)
	finally:
		await session.close()


async def get_permission_read_repository() -> AsyncIterator[SqlAlchemyPermissionReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemyPermissionReadRepository(session)
	finally:
		await session.close()


def get_event_publisher(request: Request) -> EventPublisher:
	return InMemoryEventPublisher(request.app.state.event_bus)


def get_auth_provider() -> AuthProvider:
	return ClerkJWTVerifier()


def get_webhook_verifier() -> ClerkWebhookVerifier:
	return ClerkWebhookVerifier()


async def get_verified_webhook_payload(
	request: Request,
	verifier: Annotated[ClerkWebhookVerifier, Depends(get_webhook_verifier)],
) -> dict[str, Any]:
	try:
		return dict(verifier.verify(await request.body(), request.headers))
	except Exception as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature or payload.") from exc


def get_authorization_service() -> AuthorizationService:
	return AuthorizationService()


def _command_handler(handler_type, uow, publisher=None, authorization_service=None):
	args = [uow]
	if publisher is not None:
		args.append(publisher)
	if authorization_service is not None:
		args.append(authorization_service)
	return handler_type(*args)


def get_create_user_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)]) -> CreateUserHandler: return _command_handler(CreateUserHandler, uow, publisher)
def get_update_user_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)]) -> UpdateUserHandler: return _command_handler(UpdateUserHandler, uow, publisher)
def get_deactivate_user_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)]) -> DeactivateUserHandler: return _command_handler(DeactivateUserHandler, uow, publisher)
def get_activate_user_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)]) -> ActivateUserHandler: return _command_handler(ActivateUserHandler, uow, publisher)
def get_create_role_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)]) -> CreateRoleHandler: return _command_handler(CreateRoleHandler, uow)
def get_set_user_role_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)]) -> SetUserRoleHandler: return _command_handler(SetUserRoleHandler, uow, publisher)
def get_grant_permission_to_role_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)]) -> GrantPermissionToRoleHandler: return _command_handler(GrantPermissionToRoleHandler, uow, publisher)
def get_revoke_permission_from_role_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)]) -> RevokePermissionFromRoleHandler: return _command_handler(RevokePermissionFromRoleHandler, uow, publisher)
def get_grant_permission_to_user_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)], service: Annotated[AuthorizationService, Depends(get_authorization_service)]) -> GrantPermissionToUserHandler: return _command_handler(GrantPermissionToUserHandler, uow, publisher, service)
def get_revoke_permission_from_user_handler(uow: Annotated[SqlAlchemyUnitOfWork, Depends(get_unit_of_work)], publisher: Annotated[EventPublisher, Depends(get_event_publisher)], service: Annotated[AuthorizationService, Depends(get_authorization_service)]) -> RevokePermissionFromUserHandler: return _command_handler(RevokePermissionFromUserHandler, uow, publisher, service)


def _read_handler(handler_type, repository): return handler_type(repository)
def get_user_handler(repo: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]) -> GetUserHandler: return _read_handler(GetUserHandler, repo)
def get_list_users_handler(repo: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]) -> ListUsersHandler: return _read_handler(ListUsersHandler, repo)
def get_user_role_handler(repo: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]) -> GetUserRoleHandler: return _read_handler(GetUserRoleHandler, repo)
def get_user_direct_permissions_handler(repo: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]) -> GetUserDirectPermissionsHandler: return _read_handler(GetUserDirectPermissionsHandler, repo)
def get_user_revoked_permissions_handler(repo: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)]) -> GetUserRevokedPermissionsHandler: return _read_handler(GetUserRevokedPermissionsHandler, repo)
def get_role_handler(repo: Annotated[SqlAlchemyRoleReadRepository, Depends(get_role_read_repository)]) -> GetRoleHandler: return _read_handler(GetRoleHandler, repo)
def get_list_roles_handler(repo: Annotated[SqlAlchemyRoleReadRepository, Depends(get_role_read_repository)]) -> ListRolesHandler: return _read_handler(ListRolesHandler, repo)
def get_role_permissions_handler(repo: Annotated[SqlAlchemyRoleReadRepository, Depends(get_role_read_repository)]) -> GetRolePermissionsHandler: return _read_handler(GetRolePermissionsHandler, repo)
def get_permission_handler(repo: Annotated[SqlAlchemyPermissionReadRepository, Depends(get_permission_read_repository)]) -> GetPermissionHandler: return _read_handler(GetPermissionHandler, repo)
def get_list_permissions_handler(repo: Annotated[SqlAlchemyPermissionReadRepository, Depends(get_permission_read_repository)]) -> ListPermissionsHandler: return _read_handler(ListPermissionsHandler, repo)
def get_effective_permissions_handler(repo: Annotated[SqlAlchemyPermissionReadRepository, Depends(get_permission_read_repository)]) -> GetEffectivePermissionsHandler: return _read_handler(GetEffectivePermissionsHandler, repo)
def get_current_user_profile_handler(user_repo: Annotated[SqlAlchemyUserReadRepository, Depends(get_user_read_repository)], permission_repo: Annotated[SqlAlchemyPermissionReadRepository, Depends(get_permission_read_repository)]) -> GetCurrentUserProfileHandler: return GetCurrentUserProfileHandler(user_repo, permission_repo)
