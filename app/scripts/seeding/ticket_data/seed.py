from __future__ import annotations

import asyncio
import logging
from uuid import UUID, uuid4

from sqlalchemy import delete

from app.modules.auth.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork as AuthUnitOfWork
from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel
from app.modules.ticket_management.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork as TicketUnitOfWork
from app.shared.database.engine import engine
from app.scripts.seeding.ticket_data.processed_tickets import ProcessedTicket, load_processed_tickets
from app.modules.auth.domain.value_objects.person_name import name_orderings, normalize_full_name
from app.scripts.seeding.users.historical_users import HISTORICAL_USERS

logger = logging.getLogger(__name__)

RESOLUTION_NOTES_PLACEHOLDER = "No resolution notes recorded."


async def _build_assignee_lookup() -> dict[str, UUID]:
	"""Map every spelling of each historical user's name to their seeded auth user id.

	Both orderings, keyed the way `normalize_full_name` writes them, because the dataset names
	its actors in whichever order its author used -- the same reason the batch import's own
	lookup matches either way round. Keying on one spelling would fail the two engineers the
	catalog records given-name-first.
	"""
	lookup: dict[str, UUID] = {}
	async with AuthUnitOfWork() as uow:
		for definition in HISTORICAL_USERS:
			user = await uow.users.get_by_email(definition.email)
			if user is None:
				raise ValueError(f"Historical user not seeded: {definition.display_name} ({definition.email})")
			for spelling in name_orderings(definition.first_name, definition.last_name):
				lookup[spelling] = user.id
	return lookup


def _build_ticket(row: ProcessedTicket, assignee_id: UUID) -> Ticket:
	ticket = Ticket.create(
		id=uuid4(),
		title=row.title,
		description=row.description,
		priority=row.priority,
		created_at=row.created_at,
		application=row.application,
		assignee_id=assignee_id,
		category=row.category,
		functional_team=row.functional_team,
		genergy_id=row.genergy_id,
		oceane_id=row.oceane_id,
		jira_id=row.jira_id,
		jira_delivery_date=row.jira_delivery_date,
		requires_jira=row.requires_jira,
		operational_highlight=row.operational_highlight,
		offer=row.offer,
		version=row.version,
		element=row.element,
		vio_app=row.vio_app,
	)
	ticket.start_progress(row.created_at)

	transfer_destination = row.transferred_to
	if transfer_destination is not None and transfer_destination.is_origin_of(row.functional_team, row.application):
		# Historical data glitch: the ticket was recorded as transferred to its own
		# team/application, which the domain treats as a no-op transfer. Reconstruct
		# it as a normal resolution instead of forcing an invalid transfer.
		transfer_destination = None

	if transfer_destination is not None:
		ticket.transfer(transfer_destination, row.created_at)
		ticket.close(row.closed_at)
		ticket.resolution_notes = row.resolution_notes
	else:
		notes = row.resolution_notes or RESOLUTION_NOTES_PLACEHOLDER
		resolved_at = row.resolved_at or row.closed_at
		ticket.resolve(notes, resolved_at)
		ticket.close(row.closed_at)

	return ticket


async def _clear_historical_tickets(uow: TicketUnitOfWork) -> None:
	await uow.session.execute(delete(TicketModel))


async def seed_historical_tickets(uow: TicketUnitOfWork, assignee_lookup: dict[str, UUID]) -> None:
	await _clear_historical_tickets(uow)
	for row in load_processed_tickets():
		assignee_id = assignee_lookup[normalize_full_name(row.acteur)]
		ticket = _build_ticket(row, assignee_id)
		await uow.tickets.add(ticket)


async def seed_database() -> None:
	assignee_lookup = await _build_assignee_lookup()
	async with TicketUnitOfWork() as uow:
		try:
			await seed_historical_tickets(uow, assignee_lookup)
			await uow.commit()
		except Exception:
			logger.exception("Historical ticket seeding failed")
			raise
	logger.info("Historical tickets imported")
	await engine.dispose()


def main() -> None:
	asyncio.run(seed_database())


if __name__ == "__main__":
	main()
