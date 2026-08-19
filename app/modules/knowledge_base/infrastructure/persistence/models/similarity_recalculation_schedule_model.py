from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database.base import Base

# There is one schedule for the installation, so there is one row, and its key is a constant rather
# than a generated id: nothing refers to this row from anywhere, so an identity that varied would
# only make "the schedule" something you have to look up before you can read it.
SINGLETON_ID = 1


class SimilarityRecalculationScheduleModel(Base):
	"""The configured schedule for the full similarity graph recalculation.

	Singleton enforced in the database rather than by convention: a second row here would be a
	second answer to "when does the rebuild run", and whichever one the code happened to read would
	quietly win. The check constraint makes that unrepresentable instead of unlikely.

	The table can be empty, and that is the normal state of a fresh installation -- no row means no
	administrator has configured anything and the defaults in the domain are in force. Nothing
	seeds it, so the defaults have exactly one home.
	"""

	__tablename__ = "similarity_recalculation_schedule"
	__table_args__ = (
		CheckConstraint(f"id = {SINGLETON_ID}", name="ck_similarity_recalculation_schedule_singleton"),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
	enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
	# The three-letter cron codes the domain enum is valued as, stored as an array rather than a
	# joined string so the column holds a set of days rather than a format to be parsed.
	days_of_week: Mapped[list[str]] = mapped_column(ARRAY(String(3)), nullable=False)
	hour: Mapped[int] = mapped_column(Integer, nullable=False)
	minute: Mapped[int] = mapped_column(Integer, nullable=False)
	# An IANA zone name, not an offset: a schedule set for 20:00 local time stays at 20:00 across a
	# daylight-saving change, which a stored offset could not do.
	timezone: Mapped[str] = mapped_column(String(64), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	# Nullable for the same reason audit entries' actor is: a row could in principle be written by
	# something other than an authenticated administrator. Every path that writes one today carries
	# a real actor.
	updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
