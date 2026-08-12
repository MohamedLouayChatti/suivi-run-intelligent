from __future__ import annotations

from enum import StrEnum


class KnowledgeSourceType(StrEnum):
	"""Origin of a KnowledgeItem's content. One member in V1 -- see knowledge_base/CLAUDE.md §4."""

	TICKET = "TICKET"
