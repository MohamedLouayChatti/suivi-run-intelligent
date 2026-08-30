from __future__ import annotations

import logging
from uuid import UUID

from app.modules.auth.application.interfaces.user_read_repository import UserReadRepository
from app.modules.ticket_management.application.commands.import_tickets import columns as column_contract
from app.modules.ticket_management.application.commands.import_tickets.command import ImportTicketsCommand
from app.modules.ticket_management.application.commands.import_tickets.columns import ResolvedColumns
from app.modules.ticket_management.application.commands.import_tickets.record_parser import (
	ParsedTicketRecord,
	parse_record,
)
from app.modules.ticket_management.application.commands.import_tickets.ticket_builder import (
	build_ticket,
	describe_domain_error,
)
from app.modules.ticket_management.application.dto.ticket_dto import TicketContentDTO
from app.modules.ticket_management.application.dto.ticket_identity_key import TicketIdentityKey
from app.modules.ticket_management.application.dto.ticket_import_dto import (
	TicketImportErrorDTO,
	TicketImportRecord,
	TicketImportReportDTO,
)
from app.modules.ticket_management.application.exceptions import TicketImportRejected
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.events.tickets_imported import TicketsImported
from app.modules.ticket_management.domain.exceptions import TicketDomainError
from app.shared.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)

# The header row is line 1 of the file, so a problem with the header is reported against it rather
# than against no line at all -- an operator's editor and this report then agree about where to
# look.
_HEADER_LINE = 1


class ImportTicketsHandler:
	"""Validates a whole file, then creates every ticket in it in one transaction, or creates none.

	All-or-nothing is not a convenience here, it is the only useful contract for a bulk load: a
	partially applied import leaves an operator to work out which of a thousand rows landed, and
	re-running the file would then duplicate exactly the ones that did. So nothing is written until
	every row has been shown to be a ticket this module would have accepted anyway.

	Every row is checked, not just up to the first bad one, and the whole list comes back at once.
	Fixing an export is an edit-and-retry loop, and a validator that reveals one problem per attempt
	turns a thirty-second fix into a morning.

	The domain does the deciding wherever it already has an opinion. Conditional application fields,
	legal transitions, chronology and blank-text rules are checked by building the aggregate and
	letting it refuse, never by a second implementation of the same rules that would be free to
	drift from the one the API uses. What is checked here is only what the aggregate cannot see:
	the shape of the file, whether a status has the companion columns its replay needs, whether the
	named assignee resolves to exactly one user, and whether the batch duplicates tickets that
	already exist.
	"""

	def __init__(
		self,
		uow: UnitOfWork,
		event_publisher: EventPublisher,
		ticket_read_repository: TicketReadRepository,
		users: UserReadRepository,
	) -> None:
		self.uow = uow
		self.event_publisher = event_publisher
		self.ticket_read_repository = ticket_read_repository
		self.users = users

	async def handle(self, command: ImportTicketsCommand) -> TicketImportReportDTO:
		resolved = self._reject_unusable_file(command)

		errors: list[TicketImportErrorDTO] = []
		parsed: list[ParsedTicketRecord] = []
		for record in command.records:
			record_parsed, record_errors = parse_record(self._canonicalize(record, resolved))
			errors.extend(record_errors)
			if record_parsed is not None:
				parsed.append(record_parsed)

		assignees = await self._resolve_assignees(parsed, errors)
		await self._reject_duplicates(parsed, errors)
		tickets, contents = self._build(parsed, command, assignees, errors)

		if errors:
			raise TicketImportRejected(errors)

		# One transaction for the whole file, which is the entire point: every ticket the file
		# describes is staged and committed together, so an interruption anywhere leaves none of
		# them rather than an arbitrary prefix nobody can identify afterwards.
		for ticket in tickets:
			await self.uow.tickets.add(ticket)
		try:
			await self.uow.commit()
		except Exception:
			await self.uow.rollback()
			raise

		ticket_ids = tuple(ticket.id for ticket in tickets)
		await self.event_publisher.publish(
			TicketsImported(
				application=command.application,
				ticket_ids=ticket_ids,
				occurred_at=command.imported_at,
				actor_id=command.actor_id,
			)
		)
		logger.info(
			"Imported %d %s ticket(s) from a file uploaded by %s.",
			len(ticket_ids), command.application.value, command.actor_id,
		)
		return TicketImportReportDTO(
			application=command.application, ticket_ids=ticket_ids, contents=tuple(contents)
		)

	def _reject_unusable_file(self, command: ImportTicketsCommand) -> ResolvedColumns:
		"""Stops before the rows when the file cannot be read against the contract at all.

		A misspelled or missing column would otherwise fail every single row for the same reason,
		burying the one real problem under a thousand consequences of it.
		"""
		resolved = column_contract.resolve_columns(command.columns)
		if resolved.problems:
			raise TicketImportRejected(
				[TicketImportErrorDTO(line_number=_HEADER_LINE, message=message) for message in resolved.problems]
			)
		if not command.records:
			raise TicketImportRejected(
				[
					TicketImportErrorDTO(
						line_number=_HEADER_LINE,
						message="Le fichier ne contient aucune ligne de ticket sous l'en-tête.",
					)
				]
			)
		return resolved

	def _canonicalize(self, record: TicketImportRecord, resolved: ResolvedColumns) -> TicketImportRecord:
		"""Re-key one record from the headers the file used onto the column names this module reads by.

		Done once, here, so that everything downstream -- the parser, the error messages, the
		conditional rules -- works in one vocabulary regardless of how a header happened to be
		spelled, accented or punctuated. It is also what keeps the reader that produced these
		records free of any column knowledge: it hands over whatever the header row said, and the
		module that owns the contract decides what those words meant.
		"""
		return TicketImportRecord(
			line_number=record.line_number,
			values={
				column: record.values.get(header, "") for header, column in resolved.by_header.items()
			},
		)

	async def _resolve_assignees(
		self, parsed: list[ParsedTicketRecord], errors: list[TicketImportErrorDTO]
	) -> dict[str, UUID]:
		"""Maps each distinct assignee name in the file to the one user it names.

		One query for the whole file rather than one per row: a file of a thousand tickets is
		typically written by a handful of engineers, so the number of names is small and the number
		of rows is not.

		Both failure modes are rejections rather than guesses. A name matching nobody is the check
		this was asked for -- an import may not invent people. A name matching two people is
		possible because a name carries no unique constraint, and choosing between them would
		attribute someone's work to a colleague on the strength of a coin flip.

		Which spellings answer to a name is the directory's rule, not this module's: the lookup
		matches either order the two halves are written in, so a file naming someone the way its
		author says it aloud resolves the same person as one following the export convention.

		Active and inactive users alike are accepted. The question is whether the person exists,
		not whether they still work here: the historical engineers these files are full of are
		seeded deactivated, and a ticket already keeps its assignee when that user is deactivated
		later.
		"""
		names = {record.assignee_name for record in parsed}
		if not names:
			return {}

		matches = await self.users.find_by_display_names(sorted(names))
		resolved = {name: found[0].id for name, found in matches.items() if len(found) == 1}
		ambiguous = {name for name, found in matches.items() if len(found) > 1}

		for record in parsed:
			if record.assignee_name in resolved:
				continue
			message = (
				f"« {record.assignee_name} » correspond à plusieurs utilisateurs : l'acteur est "
				f"ambigu. Utilisez un nom d'affichage qui ne désigne qu'une seule personne."
				if record.assignee_name in ambiguous
				else f"« {record.assignee_name} » ne correspond à aucun utilisateur enregistré. "
				f"Vérifiez l'orthographe du nom d'affichage."
			)
			errors.append(
				TicketImportErrorDTO(
					line_number=record.line_number,
					message=message,
					column=column_contract.ASSIGNEE,
					value=record.assignee_name,
				)
			)
		return resolved

	async def _reject_duplicates(
		self, parsed: list[ParsedTicketRecord], errors: list[TicketImportErrorDTO]
	) -> None:
		"""Rejects rows that repeat another row, or a ticket that already exists.

		Re-uploading a file is the likeliest thing to go wrong with an import, and it is silent:
		nothing in the schema stops the same incident being stored twice, and the second copy then
		sits at the top of the first one's similar-incident results forever, matching itself.

		Identity is the whole triple -- genergy_id, oceane_id and description together -- because
		neither identifier is unique or even always present in this data, so either alone would
		reject rows that are genuinely different incidents.
		"""
		keys = {
			record.line_number: TicketIdentityKey.of(
				genergy_id=record.genergy_id,
				oceane_id=record.oceane_id,
				description=record.description,
			)
			for record in parsed
		}
		if not keys:
			return

		existing = await self.ticket_read_repository.find_existing_identity_keys(list(set(keys.values())))

		first_seen: dict[TicketIdentityKey, int] = {}
		for line_number, key in keys.items():
			if key in existing:
				errors.append(
					TicketImportErrorDTO(
						line_number=line_number,
						message=(
							"Ce ticket existe déjà en base : mêmes « id genergy », « id oceane » et "
							"« description »."
						),
					)
				)
			elif key in first_seen:
				errors.append(
					TicketImportErrorDTO(
						line_number=line_number,
						message=(
							f"Cette ligne fait doublon avec la ligne {first_seen[key]} : mêmes "
							f"« id genergy », « id oceane » et « description »."
						),
					)
				)
			else:
				first_seen[key] = line_number

	def _build(
		self,
		parsed: list[ParsedTicketRecord],
		command: ImportTicketsCommand,
		assignees: dict[str, UUID],
		errors: list[TicketImportErrorDTO],
	) -> tuple[list[Ticket], list[TicketContentDTO]]:
		"""Builds every aggregate the file describes, letting the domain reject what it will not accept.

		Built before anything is written, and that ordering is what the all-or-nothing promise rests
		on: the conditional-field and transition rules live in the aggregate, so the only way to
		know a file satisfies them is to construct all of it first and persist afterwards.

		The contents projection is produced here, in the records' own order, so that a caller which
		has already processed those descriptions can pair its work with the tickets they became
		without reading anything back.
		"""
		tickets: list[Ticket] = []
		contents: list[TicketContentDTO] = []
		for record in parsed:
			assignee_id = assignees.get(record.assignee_name)
			if assignee_id is None:
				continue
			try:
				ticket = build_ticket(record, application=command.application, assignee_id=assignee_id)
			except TicketDomainError as error:
				errors.append(
					TicketImportErrorDTO(line_number=record.line_number, message=describe_domain_error(error))
				)
				continue
			tickets.append(ticket)
			contents.append(
				TicketContentDTO(
					id=ticket.id,
					application=ticket.application,
					description=ticket.description,
					genergy_id=ticket.genergy_id,
					oceane_id=ticket.oceane_id,
				)
			)
		return tickets, contents
