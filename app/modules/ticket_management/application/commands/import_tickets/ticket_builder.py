from __future__ import annotations

from uuid import UUID, uuid4

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
_DOMAIN_ERROR_MESSAGES: dict[type[TicketDomainError], str] = {
	EmptyTitle: "title must not be blank.",
	EmptyDescription: "description must not be blank.",
	JiraIdRequired: "jira_id is required when requires_jira is true.",
	ConditionalFieldForbidden: (
		"the application-specific columns do not match this file's application: COLORIS tickets "
		"carry offer and version, AERO tickets carry element, VIO tickets carry vio_app, FCI "
		"tickets carry none of them -- and jira_id is only allowed when requires_jira is true."
	),
	OfferRequired: "offer is required for a COLORIS ticket.",
	VersionRequired: "version is required for a COLORIS ticket.",
	ElementRequired: "element is required for an AERO ticket.",
	VioAppRequired: "vio_app is required for a VIO ticket.",
	ResolutionNotesRequired: "resolution_notes must not be blank for a resolved ticket.",
	TransferDestinationIsOrigin: (
		"transferred_to is the ticket's own team and application, which is not a transfer."
	),
	ChronologicalOrderViolation: (
		"the lifecycle dates are out of order: created_at, resolved_at and closed_at must not go "
		"backwards."
	),
	InvalidStatusTransition: "the lifecycle columns do not describe a sequence a ticket can go through.",
}


def describe_domain_error(error: TicketDomainError) -> str:
	return _DOMAIN_ERROR_MESSAGES.get(type(error), type(error).__name__)


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
