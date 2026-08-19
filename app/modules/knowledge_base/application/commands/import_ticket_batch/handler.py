from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from app.modules.knowledge_base.application.commands.import_ticket_batch.command import (
	MAX_ROWS,
	MAX_UPLOAD_BYTES,
	ImportTicketBatchCommand,
)
from app.modules.knowledge_base.application.commands.import_ticket_batch.table_reader import read_table
from app.modules.knowledge_base.application.dto.batch_import_report_dto import BatchImportReportDTO
from app.modules.knowledge_base.application.exceptions import (
	BatchImportCorpusWriteFailed,
	BatchImportPreflightFailed,
	BatchImportTooLarge,
	KnowledgeBaseApplicationError,
	RecalculationAlreadyRunning,
)
from app.modules.knowledge_base.application.interfaces.recalculation_runner import RecalculationRunner
from app.modules.knowledge_base.application.services.corpus_ingestion import CorpusIngestion
from app.modules.knowledge_base.application.support.recalculation_job import SIMILARITY_RECALCULATION_JOB_NAME
from app.modules.knowledge_base.domain.entities.knowledge_item import TicketKnowledgeItem
from app.modules.knowledge_base.domain.repositories.knowledge_item_repository import KnowledgeItemRepository
from app.modules.ticket_management.application.commands.discard_imported_tickets.command import (
	DiscardImportedTicketsCommand,
)
from app.modules.ticket_management.application.commands.discard_imported_tickets.handler import (
	DiscardImportedTicketsHandler,
)
from app.modules.ticket_management.application.commands.import_tickets.command import ImportTicketsCommand
from app.modules.ticket_management.application.commands.import_tickets.handler import ImportTicketsHandler
from app.modules.ticket_management.application.dto.ticket_import_dto import TicketImportReportDTO
from app.workers.jobs import JobQueue

logger = logging.getLogger(__name__)

# The corpus is written in chunks rather than as one call: a few thousand 1024-dimension vectors is
# a payload large enough that one request is worth not building, and a chunk that fails still tells
# the compensation exactly which sources to remove, because it knows every chunk it has sent.
_CORPUS_WRITE_CHUNK = 128


class ImportTicketBatchHandler:
	"""Loads a file of tickets into the database and the knowledge base as one operation.

	This is the only place in the codebase where one request drives two modules' writes, and the
	sequence is what makes that defensible. Ticket Management owns the file's contents entirely --
	it validates every row and creates every ticket in one transaction, or creates none and reports
	why. This handler owns what happens to a ticket afterwards: embedding it, storing it in the
	corpus, and asking for the similarity graph to be rebuilt over the enlarged corpus. Neither
	module learns anything about the other's rules; Ticket Management in particular is not aware
	that this module, or any embedding pipeline, exists.

	**Atomicity, and its one honest limit.** Validation is all-or-nothing by construction: nothing
	is written until every row has been shown to be a ticket the domain would have accepted. The
	tickets then land in one Postgres transaction. The corpus is a second store with no transaction
	shared with the first, so the guarantee there is a compensating one rather than a transactional
	one -- if the embedding or the corpus write fails, the tickets that were just created are
	deleted again and the whole import is reported as failed. The outcome an operator sees is the
	one they were promised, all or nothing, and the narrow window in between is not observable from
	outside this call.

	The alternative -- embedding first, so nothing is ever written on a failure -- was considered
	and rejected. It would have to read the description column out of the file to know what to
	embed, putting knowledge of the ticket schema in this module purely to reorder two steps, and
	it would spend a full pass of model calls on files that turn out to be invalid, which is the
	common failure rather than the rare one. What it buys over compensating is that a failed
	import writes nothing rather than writing and unwinding, and those are the same import.

	**The rebuild is not part of the transaction, and could not be.** It walks the entire corpus
	and takes minutes, so it is enqueued on the same single-flight runner the schedule and the
	manual trigger already share, and the response says it was accepted rather than that it
	finished. A pass already in flight makes the whole import refuse up front, before anything is
	read or written: the alternative is an import whose tickets sit outside the graph until the
	next scheduled pass, days later, which defeats the point of importing them.
	"""

	def __init__(
		self,
		import_tickets: ImportTicketsHandler,
		discard_imported_tickets: DiscardImportedTicketsHandler,
		knowledge_items: KnowledgeItemRepository,
		ingestion: CorpusIngestion,
		runner: RecalculationRunner,
		job_queue: JobQueue,
	) -> None:
		self.import_tickets = import_tickets
		self.discard_imported_tickets = discard_imported_tickets
		self.knowledge_items = knowledge_items
		self.ingestion = ingestion
		self.runner = runner
		self.job_queue = job_queue

	async def handle(self, command: ImportTicketBatchCommand) -> BatchImportReportDTO:
		self._reject_oversized_upload(command)
		# Before the file is even read. Everything after this point either creates tickets or costs
		# model calls, and none of it is worth doing for an import that is about to be refused.
		if self.runner.is_running:
			raise RecalculationAlreadyRunning()

		parsed = read_table(command.content, command.file_name)
		if len(parsed.records) > MAX_ROWS:
			raise BatchImportTooLarge(
				f"The file has {len(parsed.records)} rows, which is more than the {MAX_ROWS} an "
				f"import accepts. Split it and upload the parts separately."
			)

		await self._preflight()

		report = await self.import_tickets.handle(
			ImportTicketsCommand(
				application=command.application,
				columns=parsed.columns,
				records=parsed.records,
				imported_at=command.imported_at,
				actor_id=command.actor_id,
			)
		)

		written, skipped = await self._populate_corpus(report, command)
		enqueued = await self._request_recalculation()

		logger.info(
			"Batch import of %s%s completed: %d %s ticket(s) created, %d knowledge item(s) written, "
			"%d skipped for having no text to embed.",
			command.file_name, f" (sheet {parsed.sheet_name})" if parsed.sheet_name else "",
			len(report.ticket_ids), command.application.value, written, skipped,
		)
		return BatchImportReportDTO(
			application=command.application,
			tickets_imported=len(report.ticket_ids),
			knowledge_items_written=written,
			skipped_empty_text=skipped,
			recalculation_enqueued=enqueued,
			sheet_name=parsed.sheet_name,
		)

	async def _preflight(self) -> None:
		"""Establishes that this import can succeed before it creates anything.

		An unreachable embedding provider, or a corpus some other model produced, makes the whole
		operation impossible -- and finding that out here costs a round trip, where finding it out
		afterwards costs a transaction and the rollback of one.

		Only unexpected failures are re-labelled. MixedEmbeddingCorpus is this module's own
		diagnosis of a real corpus problem and already says what to do about it, so wrapping it in
		a connectivity message would replace an accurate answer with a misleading one.
		"""
		try:
			await self.ingestion.prepare(self.knowledge_items)
		except KnowledgeBaseApplicationError:
			raise
		except Exception as error:
			logger.exception("Batch import refused: the knowledge base could not be reached.")
			raise BatchImportPreflightFailed(str(error) or type(error).__name__) from error

	def _reject_oversized_upload(self, command: ImportTicketBatchCommand) -> None:
		if len(command.content) > MAX_UPLOAD_BYTES:
			raise BatchImportTooLarge(
				f"The file is larger than the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB an import accepts."
			)

	async def _populate_corpus(
		self, report: TicketImportReportDTO, command: ImportTicketBatchCommand
	) -> tuple[int, int]:
		"""Embeds every imported ticket and stores the result, undoing the import if it cannot.

		Both halves are remote calls that can fail independently, and both are covered by the same
		compensation, because from outside they are one failure: the tickets exist and the
		knowledge base does not know about them. `written` is tracked as the work proceeds rather
		than inferred at the end, so an unwind removes exactly the points that landed.
		"""
		items: list[TicketKnowledgeItem] = []
		written: list[UUID] = []
		try:
			for content in report.contents:
				item = await self.ingestion.item_for(content, command.imported_at)
				if item is not None:
					items.append(item)

			for start in range(0, len(items), _CORPUS_WRITE_CHUNK):
				chunk = items[start : start + _CORPUS_WRITE_CHUNK]
				await self.knowledge_items.add_many(chunk)
				written.extend(item.source_id for item in chunk)
		except Exception as error:
			logger.exception("Batch import of %s failed while populating the corpus.", command.file_name)
			discarded = await self._unwind(report, command, written, reason=str(error) or type(error).__name__)
			raise BatchImportCorpusWriteFailed(
				str(error) or type(error).__name__, tickets_discarded=discarded
			) from error

		return len(items), len(report.contents) - len(items)

	async def _unwind(
		self,
		report: TicketImportReportDTO,
		command: ImportTicketBatchCommand,
		written: Sequence[UUID],
		*,
		reason: str,
	) -> bool:
		"""Takes back everything this import had managed to write, and says whether it succeeded.

		The corpus goes first and the tickets second, the same order `--reset` uses and for the
		same reason: a knowledge item whose ticket no longer exists is the state being escaped,
		while a ticket that has briefly lost its knowledge item is simply a ticket awaiting a
		backfill.

		A failure to unwind is caught rather than raised. The caller is already reporting a failed
		import, and replacing that message with the compensation's own exception would hide both
		what went wrong and the fact that something was left behind -- which is exactly what the
		operator needs to be told, since it changes the repair from "upload the file again" to
		"run the backfill".
		"""
		try:
			await self.knowledge_items.delete_by_source_ids(list(written))
			await self.discard_imported_tickets.handle(
				DiscardImportedTicketsCommand(
					ticket_ids=report.ticket_ids,
					application=report.application,
					reason=reason,
					discarded_at=command.imported_at,
					actor_id=command.actor_id,
				)
			)
		except Exception:
			logger.exception(
				"Could not roll back the batch import of %s: %d ticket(s) remain in the database "
				"without knowledge base entries. Run the knowledge base backfill to repair this.",
				command.file_name, len(report.ticket_ids),
			)
			return False
		return True

	async def _request_recalculation(self) -> bool:
		"""Asks for the whole graph to be rebuilt over the corpus this import has just enlarged.

		A full pass rather than results for the new tickets alone, because an import changes the
		graph in both directions: the imported incidents need their own neighbours, and every
		ticket already stored may now have a better match than the one it was born with. That is
		the rebuild's job by definition, and it is the same handler the schedule drives -- there is
		no import-specific recalculation to keep in step with it.

		Enqueued, never awaited. It outlives this request, so the report says it was accepted and
		its outcome goes to the log. The in-flight check at the top of the import is what makes
		that acceptance meaningful; this second check only catches a pass that started in between,
		which the runner would refuse anyway.
		"""
		if self.runner.is_running:
			logger.warning(
				"Batch import finished but a recalculation was already running, so the graph will "
				"not include the imported tickets until the next pass."
			)
			return False
		await self.job_queue.enqueue(self.runner.run, name=SIMILARITY_RECALCULATION_JOB_NAME)
		return True
