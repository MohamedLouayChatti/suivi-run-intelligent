from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecalculateApplicationHealthBaselinesCommand:
	"""No fields -- the pass always covers every Application, so there is nothing for a caller to
	choose."""
