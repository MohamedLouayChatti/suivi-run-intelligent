from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from app.modules.analytics.application.dto.user_summary_dto import UserSummaryDTO


class AnalyticsUserSummaryResponse(BaseModel):
	id: UUID
	display_name: str
	avatar_url: str | None

	@classmethod
	def from_dto(cls, user: UserSummaryDTO | None) -> AnalyticsUserSummaryResponse | None:
		return None if user is None else cls(id=user.id, display_name=user.display_name, avatar_url=user.avatar_url)
