from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ticket_management.domain.enums.application import Application
from app.shared.database.base import Base


class ApplicationHealthBaselineModel(Base):
	"""One row per Application -- the cached statistics the daily recalculation job replaces
	wholesale, never appended to. `application` mints its own Postgres enum type
	(`analytics_application`) rather than reusing Ticket Management's, mirroring Auth's
	ApplicationAssignmentModel precedent of a module minting its own copy of an enum it does not
	own the source of."""

	__tablename__ = "application_health_baselines"

	application: Mapped[Application] = mapped_column(SAEnum(Application, name="analytics_application"), primary_key=True)
	active_count_mean: Mapped[float] = mapped_column(Float, nullable=False)
	active_count_median: Mapped[float] = mapped_column(Float, nullable=False)
	active_count_max: Mapped[float] = mapped_column(Float, nullable=False)
	active_count_stddev: Mapped[float] = mapped_column(Float, nullable=False)
	active_count_sample_days: Mapped[int] = mapped_column(Integer, nullable=False)
	resolution_hours_mean: Mapped[float] = mapped_column(Float, nullable=False)
	resolution_hours_median: Mapped[float] = mapped_column(Float, nullable=False)
	resolution_hours_max: Mapped[float] = mapped_column(Float, nullable=False)
	resolution_hours_stddev: Mapped[float] = mapped_column(Float, nullable=False)
	resolution_hours_sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
	computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
