from __future__ import annotations

from enum import StrEnum


class KnowledgeSourceType(StrEnum):
	"""Origin of a KnowledgeItem's content.

	One member today. Named explicitly rather than hard-wired everywhere so that adding application
	documentation as a second source does not mean rewriting the corpus; the discriminator this
	enum backs is what keeps a Document from ever carrying a ticket's genergy_id.
	"""

	TICKET = "TICKET"
