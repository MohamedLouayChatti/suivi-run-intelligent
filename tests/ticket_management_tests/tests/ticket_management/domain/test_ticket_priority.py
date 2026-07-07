from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.exceptions import TicketArchived, TicketClosed
from tests.ticket_management.domain import factories


class TestChangePriority:
	def test_changes_priority_and_stamps_updated_at(self, open_ticket):
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.change_priority(Priority.CRITICAL, moment)

		assert open_ticket.priority == Priority.CRITICAL
		assert open_ticket.updated_at == moment

	def test_cannot_change_priority_of_a_closed_ticket(self, closed_ticket):
		with pytest.raises(TicketClosed):
			closed_ticket.change_priority(Priority.HIGH, factories.a_moment_after(closed_ticket.updated_at))

	def test_cannot_change_priority_of_an_archived_ticket(self, archived_ticket):
		with pytest.raises(TicketArchived):
			archived_ticket.change_priority(Priority.HIGH, factories.a_moment_after(archived_ticket.updated_at))
