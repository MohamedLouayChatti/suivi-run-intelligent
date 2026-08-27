from __future__ import annotations

from bisect import bisect_right
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from app.modules.analytics.application.dto.ticket_lifecycle_event_dto import TicketLifecycleEventDTO
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.enums.ticket_history_event_type import TicketHistoryEventType

_ACTIVE_STATUSES = (Status.OPEN, Status.IN_PROGRESS)


def reconstruct_daily_active_counts(events: list[TicketLifecycleEventDTO], *, as_of: date) -> list[int]:
	"""How many tickets were active (OPEN/IN_PROGRESS and not archived), on each calendar day
	from the earliest event through `as_of`.

	A real business rule -- what counts as "active on a given day" -- rather than persistence
	logic, which is why it lives in Domain and takes no session: `events` is expected to already
	be every CREATED/STATUS_CHANGED/ARCHIVED/RESTORED entry for one application, in any order.

	Each ticket's own events are replayed into a step function: the state that holds from one
	event until the next (or forever, after the last one). A day's count is read off that step
	function at a snapshot instant -- end of day for a day that has fully elapsed, and "now" for
	`as_of` itself, since a ticket cannot yet have moved beyond the moment this function runs.
	"""
	if not events:
		return []

	by_ticket: dict[UUID, list[TicketLifecycleEventDTO]] = {}
	for event in events:
		by_ticket.setdefault(event.ticket_id, []).append(event)

	# Per ticket: parallel lists of checkpoint timestamps and the active/inactive state that
	# holds from that timestamp onward. bisect_right against a snapshot instant then finds the
	# checkpoint in force at that instant in O(log n).
	timelines: list[tuple[list[datetime], list[bool]]] = []
	earliest: datetime | None = None
	for ticket_events in by_ticket.values():
		ticket_events.sort(key=lambda e: e.occurred_at)
		timestamps: list[datetime] = []
		states: list[bool] = []
		status: Status | None = None
		archived = False
		for event in ticket_events:
			if event.to_status is not None:
				status = event.to_status
			if event.event_type is TicketHistoryEventType.ARCHIVED:
				archived = True
			elif event.event_type is TicketHistoryEventType.RESTORED:
				archived = False
			timestamps.append(event.occurred_at)
			states.append(status in _ACTIVE_STATUSES and not archived)
		timelines.append((timestamps, states))
		if earliest is None or timestamps[0] < earliest:
			earliest = timestamps[0]

	assert earliest is not None
	start_day = earliest.date()

	counts: list[int] = []
	current_day = start_day
	while current_day <= as_of:
		snapshot = datetime.now(UTC) if current_day == as_of else datetime.combine(current_day, time.max, tzinfo=UTC)
		active_count = 0
		for timestamps, states in timelines:
			index = bisect_right(timestamps, snapshot) - 1
			if index >= 0 and states[index]:
				active_count += 1
		counts.append(active_count)
		current_day += timedelta(days=1)

	return counts
