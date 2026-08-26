from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
	"""A slice of a filtered result set plus how many rows the filter matched in total.

	Application-layer read handlers return this instead of a bare list wherever a caller needs
	to know how many pages exist -- the count is not a scoped/limited slice's row count, but the
	same filters' `COUNT(*)`, computed by the repository alongside the page itself.
	"""

	items: list[T]
	total: int
