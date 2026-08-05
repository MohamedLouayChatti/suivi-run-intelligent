from __future__ import annotations

import asyncio
from dataclasses import replace
from uuid import UUID

from app.modules.audit.application.dto.audit_entry_dto import AuditEntryDTO
from app.modules.audit.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class AuditUserEnricher:
	"""Decorates Audit read DTOs with user projections from Auth."""

	def __init__(self, user_repository: UserReadRepository) -> None:
		self.user_repository = user_repository

	async def _load(self, user_id: UUID | None) -> UserSummaryDTO | None:
		if user_id is None:
			return None
		user = await self.user_repository.get_user(user_id)
		return None if user is None else UserSummaryDTO(id=user.id, display_name=user.display_name, avatar_url=user.avatar_url)

	async def _load_many(self, user_ids: set[UUID]) -> dict[UUID, UserSummaryDTO | None]:
		values = await asyncio.gather(*(self._load(user_id) for user_id in user_ids))
		return dict(zip(user_ids, values, strict=True))

	async def entry(self, entry: AuditEntryDTO) -> AuditEntryDTO:
		return replace(entry, actor=await self._load(entry.actor_id))

	async def entries(self, entries: list[AuditEntryDTO]) -> list[AuditEntryDTO]:
		actor_ids = {entry.actor_id for entry in entries if entry.actor_id is not None}
		users = await self._load_many(actor_ids)
		return [replace(entry, actor=users.get(entry.actor_id)) for entry in entries]
