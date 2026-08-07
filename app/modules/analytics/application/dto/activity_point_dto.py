from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ActivityPointDTO:
	"""One bucket of the activity trend. `bucket_start` is the point's date -- locale
	formatting (e.g. "12 janv.") is presentation logic and stays in the frontend."""

	bucket_start: datetime
	created: int
	resolved: int
