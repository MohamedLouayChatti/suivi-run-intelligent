from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request

from app.shared.config.settings import Settings, get_settings
from app.shared.security.auth_provider import AuthProvider, AuthenticatedClaims


class AuthProviderConfigurationError(RuntimeError):
	"""Raised when required Authentication provider settings are missing."""


class AuthProviderError(RuntimeError):
	"""Raised when authenticator provider rejects a token or its claims are invalid."""


class _TokenRequest:
	"""Small request-shaped adapter accepted by Clerk's request authenticator."""

	def __init__(self, token: str) -> None:
		self.headers = {"Authorization": f"Bearer {token}"}


class ClerkJWTVerifier(AuthProvider):
	"""Authenticate Clerk session tokens using Clerk's official Python SDK.

	It owns token validation and claim extraction only; it does not resolve users,
	apply authorization rules, access persistence, or depend on an HTTP framework.
	"""

	def __init__(self, settings: Settings | None = None) -> None:
		self._settings = settings or get_settings()
		if not self._settings.clerk_issuer:
			raise AuthProviderConfigurationError("CLERK_ISSUER is required for JWT verification.")
		if not self._settings.clerk_jwt_key and not self._settings.clerk_secret_key:
			raise AuthProviderConfigurationError(
				"At least one of CLERK_JWT_KEY or CLERK_SECRET_KEY is required."
			)

	def authenticate(self, token: str) -> AuthenticatedClaims:
		"""Verify a Clerk JWT and return validated, provider-independent claims."""
		if not token or not token.strip():
			raise AuthProviderError("Authentication token is empty.")

		try:
			options = AuthenticateRequestOptions(
				secret_key=self._settings.clerk_secret_key,
				jwt_key = (
					self._settings.clerk_jwt_key.replace("\\n", "\n")
					if self._settings.clerk_jwt_key is not None
					else None
				),
				audience=self._settings.clerk_audience,
				authorized_parties=self._settings.clerk_authorized_parties,
				accepts_token=["session_token"],
			)
			state = authenticate_request(_TokenRequest(token), options)
		except Exception as exc:
			raise AuthProviderError("Clerk JWT verification failed.") from exc

		if not state.is_authenticated or not isinstance(state.payload, Mapping):
			reason = getattr(state, "message", None) or "Clerk JWT verification failed."
			raise AuthProviderError(str(reason))

		claims: dict[str, Any] = dict(state.payload)
		issuer = claims.get("iss")
		if not isinstance(issuer, str):
			raise AuthProviderError("JWT issuer is missing or invalid.")

		# The Python SDK deliberately disables PyJWT issuer verification and does
		# not expose an issuer option, so this remains an adapter-level check.
		if issuer != self._settings.clerk_issuer:
			raise AuthProviderError("JWT issuer is invalid.")

		subject = claims.get("sub")
		if not isinstance(subject, str) or not subject:
			raise AuthProviderError("JWT subject is missing or invalid.")

		audience = claims.get("aud")
		if isinstance(audience, list):
			audience_value: str | tuple[str, ...] | None = tuple(
				value for value in audience if isinstance(value, str)
			)
		else:
			audience_value = audience if isinstance(audience, str) else None

		return AuthenticatedClaims(
			subject=subject,
			issuer=issuer,
			audience=audience_value,
			claims=claims,
		)
