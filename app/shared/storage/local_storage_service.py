from __future__ import annotations

import asyncio
from pathlib import Path

from app.shared.config.settings import get_settings
from app.shared.storage.service import StorageService


class LocalStorageService(StorageService):
	"""Reads/writes files on the local filesystem, rooted under `root`."""

	def __init__(self, root: Path) -> None:
		self._root = root

	async def save(self, relative_path: str, content: bytes) -> None:
		path = self._root / relative_path
		await asyncio.to_thread(self._write, path, content)

	async def read(self, relative_path: str) -> bytes:
		path = self._root / relative_path
		return await asyncio.to_thread(path.read_bytes)

	@staticmethod
	def _write(path: Path, content: bytes) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_bytes(content)


storage_service: StorageService = LocalStorageService(Path(get_settings().storage_root))
