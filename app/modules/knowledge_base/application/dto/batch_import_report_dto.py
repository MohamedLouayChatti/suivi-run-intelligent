from __future__ import annotations

from dataclasses import dataclass

from app.modules.ticket_management.domain.enums.application import Application


@dataclass(frozen=True)
class BatchImportReportDTO:
	"""What one accepted batch import did, across both stores.

	Reports the corpus and the ticket counts separately because they legitimately differ:
	preprocessing can empty a description that consisted only of an order reference, and a ticket
	whose text reduces to nothing is stored without a knowledge item rather than with a vector for
	"a commande was mentioned" -- the same rule the backfill pass applies, so a ticket that arrives
	this way and one that arrives any other way are treated identically.

	`sheet_name` is the worksheet the rows came from, and is absent for a CSV. A workbook is read
	from its first sheet, so this is how an operator whose file had several finds out which one was
	used rather than wondering why half their data is missing.

	`recalculation_enqueued` is the honest end of the report. The graph rebuild outlives this
	request by design, so what can be stated is that it was accepted, not that it succeeded; its
	outcome goes to the log, where every background outcome in this codebase goes.
	"""

	application: Application
	tickets_imported: int
	knowledge_items_written: int
	skipped_empty_text: int
	recalculation_enqueued: bool
	sheet_name: str | None = None
