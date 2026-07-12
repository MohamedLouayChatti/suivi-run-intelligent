from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.exceptions import TicketArchived, TicketNotArchived
from tests.unit.ticket_management.domain import factories


class TestArchive:
	def test_archives_a_ticket(self, open_ticket):
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.archive(moment)

		assert open_ticket.archived_at == moment
		assert open_ticket.updated_at == moment

	def test_cannot_archive_an_already_archived_ticket(self, archived_ticket):
		with pytest.raises(TicketArchived):
			archived_ticket.archive(factories.a_moment_after(archived_ticket.updated_at))

	def test_a_closed_ticket_can_still_be_archived(self, closed_ticket):
		# Archiving is only blocked by an existing archive, not by CLOSED
		# status: closed tickets are the typical candidate for archiving.
		moment = factories.a_moment_after(closed_ticket.updated_at)

		closed_ticket.archive(moment)

		assert closed_ticket.archived_at == moment


class TestRestore:
	def test_restores_an_archived_ticket(self, archived_ticket):
		moment = factories.a_moment_after(archived_ticket.updated_at)

		archived_ticket.restore(moment)

		assert archived_ticket.archived_at is None
		assert archived_ticket.updated_at == moment

	def test_cannot_restore_a_ticket_that_is_not_archived(self, open_ticket):
		with pytest.raises(TicketNotArchived):
			open_ticket.restore(factories.a_moment_after(open_ticket.updated_at))
