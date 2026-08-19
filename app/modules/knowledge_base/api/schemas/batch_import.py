from __future__ import annotations

from pydantic import BaseModel

from app.modules.knowledge_base.application.dto.batch_import_report_dto import BatchImportReportDTO
from app.modules.ticket_management.application.exceptions import TicketImportRejected
from app.modules.ticket_management.domain.enums.application import Application


class BatchImportResponse(BaseModel):
	"""What an accepted import did. Every count is of something that actually happened, except the
	last, which is a request that was accepted -- named `recalculation_enqueued` rather than
	`recalculated` for that reason."""

	application: Application
	tickets_imported: int
	knowledge_items_written: int
	skipped_empty_text: int
	recalculation_enqueued: bool
	sheet_name: str | None = None

	@classmethod
	def from_dto(cls, report: BatchImportReportDTO) -> BatchImportResponse:
		return cls(
			application=report.application,
			tickets_imported=report.tickets_imported,
			knowledge_items_written=report.knowledge_items_written,
			skipped_empty_text=report.skipped_empty_text,
			recalculation_enqueued=report.recalculation_enqueued,
			sheet_name=report.sheet_name,
		)


class TicketImportErrorResponse(BaseModel):
	"""One reason one line of the file was rejected.

	`line` is the line in the uploaded file, header included, so it matches what the operator sees --
	the row number in the worksheet margin for an Excel upload, and the editor line for a CSV,
	including for the multi-line quoted descriptions these exports are full of.
	`column` and `value` are absent when the problem belongs to the row as a whole rather than to
	one cell.
	"""

	line: int
	message: str
	column: str | None = None
	value: str | None = None


class BatchImportRejectedResponse(BaseModel):
	"""The body of a rejected import: everything wrong with the file, and nothing written.

	`total_error_count` is separate from the length of `errors` on purpose. A systematically broken
	file can fail on every row, and the list is capped -- reporting the true total is what stops a
	truncated report from reading as a complete one.
	"""

	detail: str
	message: str
	total_error_count: int
	errors: list[TicketImportErrorResponse]

	@classmethod
	def from_exception(cls, exception: TicketImportRejected) -> BatchImportRejectedResponse:
		return cls(
			detail=type(exception).__name__,
			message=str(exception),
			total_error_count=exception.total_error_count,
			errors=[
				TicketImportErrorResponse(
					line=error.line_number, message=error.message, column=error.column, value=error.value
				)
				for error in exception.errors
			],
		)
