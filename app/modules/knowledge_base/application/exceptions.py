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


class RecalculationAlreadyRunning(KnowledgeBaseApplicationError):
	"""A full recalculation was requested while one was already in flight.

	A refusal rather than a queued second run, because the pass recomputes the entire graph from
	the corpus as it currently stands: one that starts immediately after another finishes writes
	the same rows a second time. Told plainly, an administrator waits; queued silently, they get an
	acknowledgement for work that will duplicate what is already happening.
	"""

	def __init__(self) -> None:
		super().__init__("A full similarity graph recalculation is already running.")


class BatchImportError(KnowledgeBaseApplicationError):
	"""Base for the ways a batch import fails outside of row validation.

	Grouped under one type so the API can answer all of them with the sentence they carry rather
	than with a bare type name. That matters more here than anywhere else in this module: a batch
	import is the one operation whose failures an operator is expected to act on themselves, and
	"BatchImportCorpusWriteFailed" tells them nothing about whether to upload the file again.
	"""


class BatchImportFileUnreadable(BatchImportError):
	"""The uploaded file could not be read as a CSV table at all.

	Distinct from a file whose rows are wrong: there is nothing to validate row by row and no list
	of problems to report, only one fact about the file. Kept separate so the answer is a plain
	sentence rather than an empty error list that looks like a bug.
	"""


class BatchImportTooLarge(BatchImportError):
	"""The upload is past the size or row ceiling the import will accept.

	Refused before the file is read rather than after, because both limits exist to bound work this
	process does in one request: every row is embedded before anything is written, and that is a
	remote call per row on the API's own event loop.
	"""


class BatchImportPreflightFailed(BatchImportError):
	"""The embedding provider or the vector store could not be reached before the import began.

	Raised while the import is still free to stop, which is the whole reason the check happens up
	front: an unreachable dependency discovered after the tickets were created would cost a
	transaction and a rollback to learn the same thing. Says explicitly that nothing was written,
	because the alternative reading -- that the file was partly applied -- is the one that stops an
	operator from simply retrying.
	"""

	def __init__(self, reason: str) -> None:
		super().__init__(
			f"The knowledge base is not reachable, so no import was attempted: {reason}. Nothing was "
			f"written and the file can be uploaded again once it is back."
		)
		self.reason = reason


class BatchImportCorpusWriteFailed(BatchImportError):
	"""The tickets were created but their vectors could not be stored, and the import was undone.

	The one failure the all-or-nothing promise has to be explicit about. The tickets are gone again
	by the time this is raised -- it reports a completed rollback, not a half-applied import -- and
	it says so in its own message rather than surfacing as a bare 500 that leaves an operator unsure
	whether to upload the file a second time.
	"""

	def __init__(self, reason: str, *, tickets_discarded: bool) -> None:
		aftermath = (
			"The imported tickets have been removed, so nothing was kept and the file can be uploaded "
			"again."
			if tickets_discarded
			else (
				"The imported tickets could NOT be removed afterwards and are still in the database "
				"without their knowledge base entries. Do not re-upload the file: run the knowledge "
				"base backfill instead, which embeds exactly the tickets that are missing an entry."
			)
		)
		super().__init__(f"The knowledge base could not be updated for this import: {reason}. {aftermath}")
		self.reason = reason
		self.tickets_discarded = tickets_discarded

