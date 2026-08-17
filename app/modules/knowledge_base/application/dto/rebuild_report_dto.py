from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RebuildReportDTO:
	"""What one similarity-graph rebuild produced.

	`sources_without_results` is reported rather than treated as a failure: a ticket with no
	sufficiently similar neighbour is a correct, expected outcome of a threshold, not a gap. It is
	worth surfacing because a rebuild where *most* sources come back empty is the signature of a
	mis-calibrated threshold, which is otherwise invisible.
	"""

	items_processed: int
	results_written: int
	sources_without_results: int
