from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.auth.application.security.user_access_policy import UserAccessPolicy
from app.modules.auth.infrastructure.persistence.repositories.sqlalchemy_user_read_repository import SqlAlchemyUserReadRepository
from app.shared.database.session import create_session
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry

def register_subscriptions(registry: SubscriptionRegistry) -> None:
    """Register Authorization event consumers."""
    return None


@asynccontextmanager
async def _user_read_repository_scope() -> AsyncIterator[UserReadRepository]:
    session = create_session()
    try:
        yield SqlAlchemyUserReadRepository(session)
    finally:
        await session.close()


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
    """Register Authorization's resource instance authorization policies."""
    registry.register("user", UserAccessPolicy(_user_read_repository_scope))