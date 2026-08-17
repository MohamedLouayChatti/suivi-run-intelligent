from __future__ import annotations

from app.shared.exceptions.application_exceptions import ApplicationError


class KnowledgeBaseApplicationError(ApplicationError):
	"""Base exception for knowledge base application errors."""


class MixedEmbeddingCorpus(KnowledgeBaseApplicationError):
	"""The stored knowledge items were not all produced by the same embedding model.

	Raised by the maintenance passes rather than tolerated, because this is a failure that hides
	itself: vectors from two models occupy unrelated coordinate spaces, so the distances between
	them are arbitrary numbers rather than errors. A graph built across a mixed corpus is
	structurally valid, passes every constraint, and is quietly meaningless -- so the only place it
	can be caught is before the work starts.

	Recovery is to re-embed the whole corpus under one model (`--reset` on the backfill CLI), not
	to embed the stragglers.
	"""

	def __init__(self, present: list[tuple[str, str]], expected: tuple[str, str] | None = None) -> None:
		found = ", ".join(f"{model}@{version}" for model, version in sorted(present))
		detail = f" Expected {expected[0]}@{expected[1]}." if expected else ""
		super().__init__(
			f"Knowledge items were produced by more than one embedding model: {found}.{detail} "
			f"Re-embed the corpus under a single model before rebuilding the similarity graph."
		)
		self.present = present
		self.expected = expected
