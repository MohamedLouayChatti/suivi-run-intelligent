from __future__ import annotations

from collections.abc import Sequence

from app.modules.ticket_management.application.dto.ticket_import_dto import TicketImportErrorDTO
from app.shared.exceptions.application_exceptions import ApplicationError

class TicketApplicationError(ApplicationError):
	"""Base exception for ticket management application errors."""


class TicketNotFound(TicketApplicationError):
	pass


class CommentNotFound(TicketApplicationError):
	pass


class AttachmentNotFound(TicketApplicationError):
	pass


class AssigneeNotFound(TicketApplicationError):
	pass


class AssigneeNotAuthorized(TicketApplicationError):
	pass


# A file with a systematically broken column can fail on every one of its rows, and returning ten
# thousand of those helps nobody and makes the response enormous. The cap is generous enough that a
# handful of scattered mistakes are all reported, and the total count is carried separately so a
# truncated report says so rather than looking complete.
MAX_REPORTED_IMPORT_ERRORS = 200


class TicketImportRejected(TicketApplicationError):
	"""A batch import was refused, and nothing was written.

	Carries every reason rather than the first one: fixing an export is an edit-and-retry loop, and
	a validator that reveals one problem per attempt turns a short fix into a long afternoon. Errors
	are ordered by line so the report reads in the same order as the file.

	The alternative -- importing the good rows and reporting the bad ones -- was rejected outright.
	It leaves an operator holding a file that is now partly applied, where the obvious next move,
	fixing it and uploading it again, duplicates everything that already landed.
	"""

	def __init__(self, errors: Sequence[TicketImportErrorDTO]) -> None:
		ordered = sorted(errors, key=lambda error: (error.line_number, error.column or "", error.message))
		self.total_error_count = len(ordered)
		self.errors = tuple(ordered[:MAX_REPORTED_IMPORT_ERRORS])
		super().__init__(
			f"Le fichier a été refusé et aucun ticket n'a été importé : {self.total_error_count} "
			f"problème(s) détecté(s)."
		)
