from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PagedResponse(BaseModel, Generic[T]):
	"""HTTP envelope for a `Page`: the current slice plus the filtered total, so a client can
	render an exact page count instead of guessing from how many rows came back."""

	items: list[T]
	total: int
