from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.analytics.domain.enums.health_level import HealthLevel
from app.modules.ticket_management.domain.enums.application import Application
from app.shared.database.base import Base


class ApplicationHealthStatusModel(Base):
	"""One row per Application -- the last known tier, written after every reactive check so the
	next one can tell a transition into CRITICAL from a re-check that finds it already there.

	Reuses the same `analytics_application` enum type ApplicationHealthBaselineModel mints --
	Alembic autogenerate must not emit a second `CREATE TYPE` for it (see the migration note in
	the model above)."""

	__tablename__ = "application_health_statuses"

	application: Mapped[Application] = mapped_column(SAEnum(Application, name="analytics_application"), primary_key=True)
	health_level: Mapped[HealthLevel] = mapped_column(SAEnum(HealthLevel, name="analytics_health_level"), nullable=False)
	active_tickets: Mapped[int] = mapped_column(Integer, nullable=False)
	avg_resolution_hours: Mapped[float] = mapped_column(Float, nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
