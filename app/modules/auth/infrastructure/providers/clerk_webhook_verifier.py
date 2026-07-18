from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from svix import Webhook

from app.shared.config.settings import Settings, get_settings


class AuthProviderWebhookConfigurationError(RuntimeError):
	"""Raised when required Authentication provider settings are missing."""


class AuthProviderWebhookError(RuntimeError):
	"""Raised when an Authentication provider encounters an error."""


class ClerkWebhookVerifier:
	"""Verify Clerk webhook signatures and return their parsed payload.

	It owns authenticity and payload parsing only; it does not handle HTTP,
	invoke application logic, synchronize users, or access persistence.
	"""
	def __init__(self, settings: Settings | None = None) -> None:
		self._settings = settings or get_settings()
		if not self._settings.clerk_webhook_signing_secret:
			raise AuthProviderWebhookConfigurationError(
				"CLERK_WEBHOOK_SIGNING_SECRET is required for webhook verification."
			)

	def verify(
		self, payload: bytes | str, headers: Mapping[str, str]
	) -> Mapping[str, Any]:
		"""Verify webhook headers and return the authenticated JSON payload."""

		secret = self._settings.clerk_webhook_signing_secret
		if secret is None:
			raise AuthProviderWebhookConfigurationError(
				"CLERK_WEBHOOK_SIGNING_SECRET is required for webhook verification."
			)

		try:
			verified = Webhook(secret).verify(payload, dict(headers))
		except Exception as exc:
			raise AuthProviderWebhookError(
				"Clerk webhook signature verification failed."
			) from exc

		if isinstance(verified, str):
			try:
				verified = json.loads(verified)
			except json.JSONDecodeError as exc:
				raise AuthProviderWebhookError(
					"Verified webhook payload is not valid JSON."
				) from exc

		if not isinstance(verified, Mapping):
			raise AuthProviderWebhookError(
				"Verified webhook payload must be an object."
			)

		return dict(verified)
