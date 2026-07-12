from __future__ import annotations

import pytest

from app.modules.ticket_management.domain.exceptions import (
	InvalidAssignee,
	TicketAlreadyAssigned,
	TicketArchived,
	TicketClosed,
	TicketNotAssigned,
)
from tests.unit.ticket_management.domain import factories


class TestAssign:
	def test_assigns_an_unassigned_ticket(self, open_ticket):
		assignee_id = factories.new_uuid()
		moment = factories.a_moment_after(open_ticket.updated_at)

		open_ticket.assign(assignee_id, moment)

		assert open_ticket.assignee_id == assignee_id
		assert open_ticket.updated_at == moment

	def test_cannot_assign_an_already_assigned_ticket(self, assigned_ticket):
		with pytest.raises(TicketAlreadyAssigned):
			assigned_ticket.assign(factories.new_uuid(), factories.a_moment_after(assigned_ticket.updated_at))

	def test_cannot_assign_with_no_assignee(self, open_ticket):
		with pytest.raises(InvalidAssignee):
			open_ticket.assign(None, factories.a_moment_after(open_ticket.updated_at))

	def test_cannot_assign_a_closed_ticket(self, closed_ticket):
		with pytest.raises(TicketClosed):
			closed_ticket.assign(factories.new_uuid(), factories.a_moment_after(closed_ticket.updated_at))

	def test_cannot_assign_an_archived_ticket(self, archived_ticket):
		with pytest.raises(TicketArchived):
			archived_ticket.assign(factories.new_uuid(), factories.a_moment_after(archived_ticket.updated_at))


class TestReassign:
	def test_reassigns_to_a_new_assignee(self, assigned_ticket):
		new_assignee = factories.new_uuid()
		moment = factories.a_moment_after(assigned_ticket.updated_at)

		assigned_ticket.reassign(new_assignee, moment)

		assert assigned_ticket.assignee_id == new_assignee
		assert assigned_ticket.updated_at == moment

	def test_cannot_reassign_an_unassigned_ticket(self, open_ticket):
		with pytest.raises(TicketNotAssigned):
			open_ticket.reassign(factories.new_uuid(), factories.a_moment_after(open_ticket.updated_at))

	def test_cannot_reassign_with_no_assignee(self, assigned_ticket):
		with pytest.raises(InvalidAssignee):
			assigned_ticket.reassign(None, factories.a_moment_after(assigned_ticket.updated_at))

	def test_cannot_reassign_a_closed_ticket(self, closed_ticket):
		with pytest.raises(TicketClosed):
			closed_ticket.reassign(factories.new_uuid(), factories.a_moment_after(closed_ticket.updated_at))
