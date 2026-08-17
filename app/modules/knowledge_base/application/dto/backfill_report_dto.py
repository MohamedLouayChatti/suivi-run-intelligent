from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BackfillReportDTO:
	"""What one backfill pass did. Returned rather than logged so the caller decides how to present
	it, and so a re-run is self-describing: on an already-complete corpus every ticket lands in
	`already_embedded` and nothing else moves, which is what "idempotent" looks like from outside.
	"""

	tickets_seen: int
	already_embedded: int
	embedded: int
	skipped_empty_text: int
