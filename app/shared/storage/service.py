from __future__ import annotations

from abc import ABC, abstractmethod


class StorageService(ABC):
	"""Port for reading/writing file bytes behind an opaque relative path.

	Application code only ever sees this abstraction — never the local filesystem,
	S3, or any other concrete backend directly.
	"""

	@abstractmethod
	async def save(self, relative_path: str, content: bytes) -> None:
		raise NotImplementedError

	@abstractmethod
	async def read(self, relative_path: str) -> bytes:
		raise NotImplementedError
