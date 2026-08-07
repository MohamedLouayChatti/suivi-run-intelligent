from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.modules.analytics.application.dto.activity_point_dto import ActivityPointDTO


class ActivityPointResponse(BaseModel):
	bucket_start: datetime
	created: int
	resolved: int

	@classmethod
	def from_dto(cls, point: ActivityPointDTO) -> ActivityPointResponse:
		return cls(bucket_start=point.bucket_start, created=point.created, resolved=point.resolved)
