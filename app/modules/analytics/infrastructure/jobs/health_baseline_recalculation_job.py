from __future__ import annotations

import logging

from app.modules.analytics.application.commands.recalculate_application_health_baselines.command import (
	RecalculateApplicationHealthBaselinesCommand,
)
from app.modules.analytics.application.commands.recalculate_application_health_baselines.handler import (
	RecalculateApplicationHealthBaselinesHandler,
)
from app.modules.analytics.infrastructure.persistence.repositories.sqlalchemy_health_history_read_repository import (
	SqlAlchemyHealthHistoryReadRepository,
)
from app.modules.analytics.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.database.session import create_session
from app.workers.jobs import WeeklySchedule

logger = logging.getLogger(__name__)

# Stable for the job's whole life -- the handle the configuration reaches for to reschedule or
# log against.
HEALTH_BASELINE_RECALCULATION_JOB_NAME = "analytics_application_health_baseline_recalculation"

# Every day, all seven days, fixed in code -- baselines only need to track a slowly-drifting
# all-time average, so daily is cheap and keeps them fresher than Knowledge Base's twice-weekly
# full pass without needing a DB-backed, admin-configurable schedule of its own.
HEALTH_BASELINE_SCHEDULE = WeeklySchedule(
	days_of_week=("mon", "tue", "wed", "thu", "fri", "sat", "sun"),
	hour=3, minute=0, timezone="UTC",
)


async def recalculate_application_health_baselines() -> None:
	"""The zero-arg job APSchedulerRunner fires daily. No in-flight guard of its own -- this job
	is only ever fired by the scheduler, and its own max_instances=1/coalesce=True already
	prevent overlap; a bespoke guard would only earn its keep once a manual "recalculate now"
	trigger exists, which this module deliberately does not have."""
	session = create_session()
	try:
		history = SqlAlchemyHealthHistoryReadRepository(session)
		handler = RecalculateApplicationHealthBaselinesHandler(history=history, uow_factory=SqlAlchemyUnitOfWork)
		await handler.handle(RecalculateApplicationHealthBaselinesCommand())
	finally:
		await session.close()
