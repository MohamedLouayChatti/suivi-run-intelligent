from __future__ import annotations

import logging

from app.modules.ticket_management.application.commands.discard_imported_tickets.command import (
	DiscardImportedTicketsCommand,
)
from app.modules.ticket_management.application.interfaces.unit_of_work import UnitOfWork
from app.modules.ticket_management.domain.events.tickets_import_discarded import TicketsImportDiscarded
from app.shared.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


class DiscardImportedTicketsHandler:
	"""Deletes the tickets one import created, in one transaction.

	Runs on a path that is already failing, which shapes everything about it: it takes ids rather
	than re-deriving them, it does no validation, and it deletes rather than archiving, because
	the tickets it is removing were never a legitimate state of the system -- they were the first
	half of an operation that turned out to have no second half.

	Failures are raised, not swallowed. A compensation that cannot complete leaves tickets with no
	entry in the knowledge base, which is recoverable -- it is the state the backfill pass exists
	to repair -- but the caller has to be able to say so rather than reporting a clean rollback
	that did not happen.
	"""

	def __init__(self, uow: UnitOfWork, event_publisher: EventPublisher) -> None:
		self.uow = uow
		self.event_publisher = event_publisher

	async def handle(self, command: DiscardImportedTicketsCommand) -> None:
		if not command.ticket_ids:
			return

		async with self.uow:
			for ticket_id in command.ticket_ids:
				await self.uow.tickets.delete(ticket_id)
			try:
				await self.uow.commit()
			except Exception:
				await self.uow.rollback()
				raise

		logger.warning(
			"Discarded %d imported %s ticket(s) after a failed batch import: %s",
			len(command.ticket_ids), command.application.value, command.reason,
		)
		await self.event_publisher.publish(
			TicketsImportDiscarded(
				application=command.application,
				ticket_ids=command.ticket_ids,
				reason=command.reason,
				occurred_at=command.discarded_at,
				actor_id=command.actor_id,
			)
		)
