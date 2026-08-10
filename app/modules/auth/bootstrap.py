from __future__ import annotations

from app.modules.auth.application.security.role_access_policy import RoleAccessPolicy
from app.modules.auth.application.security.user_access_policy import UserAccessPolicy
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry

def register_subscriptions(registry: SubscriptionRegistry) -> None:
    """Register Authorization event consumers."""
    return None


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
    """Register Authorization's resource instance authorization policies.

    Neither policy takes a repository scope: both decide entirely from `CurrentUser`
    (its id, its role ids, its effective permissions), which is already resolved once
    per request -- so neither issues a query of its own.
    """
    registry.register("user", UserAccessPolicy())
    registry.register("role", RoleAccessPolicy())