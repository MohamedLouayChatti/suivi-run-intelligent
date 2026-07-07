from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.exceptions import (
	InvalidAssignee,
	SameApplicationTransfer,
	TicketClosed,
	TicketNotAssigned,
)
from tests.ticket_management.domain import factories


class TestTransferApplication:
	def test_transfers_an_assigned_ticket_to_a_new_application(self, assigned_ticket):
		new_assignee = factories.new_uuid()
		moment = factories.a_moment_after(assigned_ticket.updated_at)

		assigned_ticket.transfer_application(Application.APP_2, new_assignee, moment)

		assert assigned_ticket.application == Application.APP_2
		assert assigned_ticket.assignee_id == new_assignee
		assert assigned_ticket.updated_at == moment

	def test_cannot_transfer_to_the_same_application(self, assigned_ticket):
		with pytest.raises(SameApplicationTransfer):
			assigned_ticket.transfer_application(
				assigned_ticket.application, factories.new_uuid(), factories.a_moment_after(assigned_ticket.updated_at)
			)

	def test_cannot_transfer_without_a_new_assignee(self, assigned_ticket):
		with pytest.raises(InvalidAssignee):
			assigned_ticket.transfer_application(
				Application.APP_2, None, factories.a_moment_after(assigned_ticket.updated_at)
			)

	def test_cannot_transfer_an_unassigned_ticket(self, open_ticket):
		with pytest.raises(TicketNotAssigned):
			open_ticket.transfer_application(
				Application.APP_2, factories.new_uuid(), factories.a_moment_after(open_ticket.updated_at)
			)

	def test_cannot_transfer_a_closed_ticket(self, closed_ticket):
		with pytest.raises(TicketClosed):
			closed_ticket.transfer_application(
				Application.APP_2, factories.new_uuid(), factories.a_moment_after(closed_ticket.updated_at)
			)
