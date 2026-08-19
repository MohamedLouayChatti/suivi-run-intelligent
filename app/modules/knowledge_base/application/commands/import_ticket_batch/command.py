from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.ticket_management.domain.enums.application import Application

# Matched to the ceiling attachments already enforce, for the same reason: it is the size past
# which an upload stops being a document somebody produced and starts being a mistake. A file of
# tickets is small -- the entire historical corpus is a few megabytes of text.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# The real constraint, and the reason it is expressed in rows rather than only in bytes: every row
# costs an embedding call before anything is written, so the row count is what decides how long a
# request runs and how much work a rejected file wastes. Well above any real export, low enough
# that a runaway file is refused rather than tying up the process for an hour.
MAX_ROWS = 5000


@dataclass(frozen=True)
class ImportTicketBatchCommand:
	"""Load one file of tickets into the database and the knowledge base, as one operation.

	`application` is chosen by the uploader and applies to the whole file -- one file, one
	application. It is carried here rather than read from a column so that the two can never
	disagree, and it is what Ticket Management stamps on every ticket the file produces.

	`content` is the file itself, CSV or Excel. The upload is read into memory in full before
	anything happens to it, which the size ceiling above is what makes safe: validation is a
	whole-file question, so there is no version of this that streams -- and a workbook is a zip
	archive, which cannot be read as a stream at all.

	`file_name` selects the reader -- CSV or Excel workbook -- and names the upload in the log. The
	file itself is not kept, since everything it asserted is in the tickets it produced.
	"""

	application: Application
	file_name: str
	content: bytes
	imported_at: datetime
	actor_id: UUID
