from __future__ import annotations

import asyncio
from dataclasses import replace
from uuid import UUID

from app.modules.analytics.application.dto.admin_overview_dto import EngineerDatumDTO, TeamOverviewDTO
from app.modules.analytics.application.dto.attention_required_dto import AttentionRequiredDTO
from app.modules.analytics.application.dto.user_summary_dto import UserSummaryDTO
from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository


class AnalyticsUserEnricher:
	"""Decorates Analytics read DTOs with user projections from Auth."""

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

	async def engineer(self, engineer_id: UUID) -> UserSummaryDTO | None:
		"""One engineer's projection, for the read models describing a single person rather
		than a list of them. None when no such user exists -- a report about somebody who has
		since been removed still has its numbers, and losing them to a missing name would be
		worse than reporting them unattributed."""
		return await self._load(engineer_id)

	async def attention_required(self, data: AttentionRequiredDTO) -> AttentionRequiredDTO:
		users = await self._load_many({incident.assignee_id for incident in data.incidents})
		return replace(
			data,
			incidents=[replace(incident, assignee=users.get(incident.assignee_id)) for incident in data.incidents],
		)

	async def team_overview(self, data: TeamOverviewDTO) -> TeamOverviewDTO:
		lists = (data.active_tickets, data.resolved_tickets, data.avg_resolution_hours, data.assignment_distribution, data.transfer_rate_pct)
		user_ids = {datum.engineer_id for entries in lists for datum in entries}
		users = await self._load_many(user_ids)

		def enrich(entries: list[EngineerDatumDTO]) -> list[EngineerDatumDTO]:
			return [replace(datum, engineer=users.get(datum.engineer_id)) for datum in entries]

		return TeamOverviewDTO(
			active_tickets=enrich(data.active_tickets),
			resolved_tickets=enrich(data.resolved_tickets),
			avg_resolution_hours=enrich(data.avg_resolution_hours),
			assignment_distribution=enrich(data.assignment_distribution),
			transfer_rate_pct=enrich(data.transfer_rate_pct),
		)
