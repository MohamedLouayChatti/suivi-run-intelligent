from __future__ import annotations

from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy


class InstanceAuthorizationRegistry:
	"""Explicit composition-root registry for resource instance policies."""

	def __init__(self) -> None:
		self._policies: dict[str, InstanceAuthorizationPolicy] = {}

	def register(self, resource_type: str, policy: InstanceAuthorizationPolicy) -> None:
		self._policies[resource_type] = policy

	def resolve(self, resource_type: str) -> InstanceAuthorizationPolicy:
		try:
			return self._policies[resource_type]
		except KeyError as exc:
			raise KeyError(f"No instance authorization policy registered for '{resource_type}'.") from exc
