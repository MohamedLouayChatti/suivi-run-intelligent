from __future__ import annotations

from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry


def register_subscriptions(registry: SubscriptionRegistry) -> None:
	"""Analytics is a pure reporting/read module: it reads directly from the operational
	database via its own dedicated read repositories and does not react to domain
	events."""
	return None


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Analytics has no single-resource instance authorization: access is gated by the
	analytics.read permission plus an application-collection scope (see
	require_analytics_applications_scope), and the admin-only overview by require_admin
	-- neither needs a per-resource_id policy in this registry."""
	return None
