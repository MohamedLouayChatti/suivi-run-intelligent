from __future__ import annotations

from uuid import UUID, uuid4

from app.modules.ticket_management.application.commands.import_tickets import columns
from app.modules.ticket_management.application.commands.import_tickets.record_parser import ParsedTicketRecord
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.exceptions import (
	ChronologicalOrderViolation,
	ConditionalFieldForbidden,
	ElementRequired,
	EmptyDescription,
	EmptyTitle,
	InvalidStatusTransition,
	JiraIdRequired,
	OfferRequired,
	ResolutionNotesRequired,
	TicketDomainError,
	TransferDestinationIsOrigin,
	VersionRequired,
	VioAppRequired,
)

# Domain errors are bare classes with no message of their own -- deliberately, since the API's
# generic translation answers with the type name and nothing else. That is unusable in an import
# report, where the reader is looking at a spreadsheet and needs to know which cell to change, so
# the ones a row can actually provoke are given a sentence here. Anything unmapped falls back to
# the type name rather than being swallowed: a new domain rule shows up as an ugly message, never
# as a silently accepted row.
#
# Each sentence names the *column* the operator has to edit rather than the aggregate's field, and
# is written in French, because the only place these are ever read is the import report -- and the
# person reading it is looking at a spreadsheet whose headers are the names below.
_DOMAIN_ERROR_MESSAGES: dict[type[TicketDomainError], str] = {
	EmptyTitle: f"La colonne « {columns.TITLE} » ne doit pas être vide.",
	EmptyDescription: f"La colonne « {columns.DESCRIPTION} » ne doit pas être vide.",
	JiraIdRequired: (
		f"La colonne « {columns.JIRA_ID} » est obligatoire lorsque « {columns.REQUIRES_JIRA} » "
		f"vaut oui."
	),
	ConditionalFieldForbidden: (
		f"Les colonnes spécifiques à une application ne correspondent pas à l'application de ce "
		f"fichier : un ticket COLORIS porte « {columns.OFFER} » et « {columns.VERSION} », un ticket "
		f"AERO porte « {columns.ELEMENT} », un ticket VIO porte « {columns.VIO_APP} », et un ticket "
		f"FCI n'en porte aucune — et « {columns.JIRA_ID} » n'est autorisée que si "
		f"« {columns.REQUIRES_JIRA} » vaut oui."
	),
	OfferRequired: f"La colonne « {columns.OFFER} » est obligatoire pour un ticket COLORIS.",
	VersionRequired: f"La colonne « {columns.VERSION} » est obligatoire pour un ticket COLORIS.",
	ElementRequired: f"La colonne « {columns.ELEMENT} » est obligatoire pour un ticket AERO.",
	VioAppRequired: f"La colonne « {columns.VIO_APP} » est obligatoire pour un ticket VIO.",
	ResolutionNotesRequired: (
		f"La colonne « {columns.RESOLUTION_NOTES} » ne doit pas être vide pour un ticket résolu."
	),
	TransferDestinationIsOrigin: (
		f"La colonne « {columns.TRANSFERRED_TO} » désigne l'équipe et l'application du ticket "
		f"lui-même, ce qui n'est pas un transfert."
	),
	ChronologicalOrderViolation: (
		f"Les dates du cycle de vie ne se suivent pas : « {columns.CREATED_AT} », "
		f"« {columns.RESOLVED_AT} » et « {columns.CLOSED_AT} » ne doivent pas revenir en arrière."
	),
	InvalidStatusTransition: (
		"Les colonnes de cycle de vie ne décrivent pas un enchaînement qu'un ticket peut suivre."
	),
}


def describe_domain_error(error: TicketDomainError) -> str:
	"""The sentence an operator reads for a row the domain refused.

	The fallback keeps the exception's type name rather than inventing a French sentence for a rule
	nobody has described yet: an unmapped error is a gap in the table above, and reading like one is
	the point -- it is reported, never swallowed, and it names exactly what to add here.
	"""
	described = _DOMAIN_ERROR_MESSAGES.get(type(error))
	if described is not None:
		return described
	return f"Cette ligne enfreint une règle métier du ticket : {type(error).__name__}."


def build_ticket(record: ParsedTicketRecord, *, application: Application, assignee_id: UUID) -> Ticket:
	"""Turn one parsed record into the aggregate it describes, replaying how it got to its status.

	Replayed rather than assembled field by field, which is the whole reason an import can be
	trusted: every invariant, every legal transition and every history entry comes from the same
	methods a ticket goes through when a person drives it, so an imported ticket and a live one are
	the same kind of object afterwards. Constructing one directly would let a file assert a state
	the domain would never have allowed anyone to reach.

	Raises TicketDomainError for a record the domain refuses. The caller turns that into a row-level
	rejection; it never repairs it, because a file that says something impossible is a file to fix
	rather than to interpret.

	Timestamps for the intermediate steps come from the row's own dates -- work starts at
	created_at and a transfer happens there too, since neither has a column of its own. The dates
	that are recorded (resolved_at, closed_at) are used where they belong, and the rest is the
	minimum consistent history that reaches the stated status.
	"""
	ticket = Ticket.create(
		id=uuid4(),
		title=record.title,
		description=record.description,
		priority=record.priority,
		created_at=record.created_at,
		application=application,
		assignee_id=assignee_id,
		category=record.category,
		functional_team=record.functional_team,
		genergy_id=record.genergy_id,
		oceane_id=record.oceane_id,
		jira_id=record.jira_id,
		jira_delivery_date=record.jira_delivery_date,
		requires_jira=record.requires_jira,
		operational_highlight=record.operational_highlight,
		offer=record.offer,
		version=record.version,
		element=record.element,
		vio_app=record.vio_app,
	)

	if record.status == Status.OPEN:
		return ticket

	ticket.start_progress(record.created_at)
	if record.status == Status.IN_PROGRESS:
		return ticket

	if record.transferred_to is not None:
		ticket.transfer(record.transferred_to, record.created_at)
	elif record.resolved_at is not None and record.resolution_notes is not None:
		ticket.resolve(record.resolution_notes, record.resolved_at)

	if record.status == Status.CLOSED and record.closed_at is not None:
		ticket.close(record.closed_at)

	return ticket
