from __future__ import annotations

from qdrant_client import AsyncQdrantClient

from app.shared.config.settings import get_settings


class QdrantNotConfigured(RuntimeError):
	"""No Qdrant endpoint is configured, so the knowledge base has nowhere to read or write."""


_client: AsyncQdrantClient | None = None


def get_qdrant_client() -> AsyncQdrantClient:
	"""The process-wide Qdrant client, mirroring the single shared AsyncEngine in
	app/shared/database/engine.py -- it holds a connection pool, so one instance per process rather
	than one per request or per event.

	Behind an accessor rather than a module-level constant, unlike the engine, for one reason: the
	endpoint is optional in settings, and building the client at import time would either crash the
	whole application on an unset variable or -- worse -- silently fall back to the client library's
	localhost default and fail much later with a connection error that names no cause.

	REST rather than gRPC. gRPC on port 6334 is measurably faster, but plain HTTPS is far likelier
	to survive a corporate network between here and Qdrant Cloud, and at this corpus size the
	transport is not what dominates a search.
	"""
	global _client
	if _client is None:
		settings = get_settings()
		if not settings.qdrant_url:
			raise QdrantNotConfigured(
				"QDRANT_CLUSTER_ENDPOINT is not set. The knowledge base stores its vectors in "
				"Qdrant, so retrieval, ingestion and the maintenance passes all need it. Set it "
				"(and QDRANT_API_KEY for a cloud cluster) in .env."
			)
		_client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
	return _client


async def close_qdrant_client() -> None:
	"""Release the client's connections. For the CLI passes, which run outside the application
	lifespan and would otherwise leave the event loop with an open pool at exit -- the same reason
	those scripts already call `engine.dispose()`."""
	global _client
	if _client is not None:
		await _client.close()
		_client = None
