"""
Tests for `Ticket.create`: the guard clauses and initial state a new
ticket must have, independent of any persistence or transport concern.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.enums.application import Application
from app.modules.ticket_management.domain.enums.priority import Priority
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.domain.exceptions import EmptyDescription, EmptyTitle, InvalidAssignee
from tests.ticket_management.domain import factories


class TestTicketCreation:
	def test_creates_ticket_with_open_status(self):
		ticket = factories.make_ticket()

		assert ticket.status == Status.OPEN

	def test_new_ticket_has_no_assignee_by_default(self):
		ticket = factories.make_ticket()

		assert ticket.assignee_id is None

	def test_new_ticket_updated_at_equals_created_at(self):
		created_at = datetime(2026, 3, 1, tzinfo=timezone.utc)

		ticket = factories.make_ticket(created_at=created_at)

		assert ticket.updated_at == created_at

	def test_new_ticket_is_not_archived(self):
		ticket = factories.make_ticket()

		assert ticket.archived_at is None

	def test_new_ticket_has_no_comments_or_attachments(self):
		ticket = factories.make_ticket()

		assert ticket.comments == []
		assert ticket.attachments == []

	def test_new_ticket_can_be_created_with_an_assignee(self):
		assignee_id = factories.new_uuid()

		ticket = factories.make_ticket(assignee_id=assignee_id)

		assert ticket.assignee_id == assignee_id

	def test_preserves_provided_application_and_priority(self):
		ticket = factories.make_ticket(application=Application.APP_3, priority=Priority.CRITICAL)

		assert ticket.application == Application.APP_3
		assert ticket.priority == Priority.CRITICAL

	@pytest.mark.parametrize("blank_title", ["", "   ", "\t\n"])
	def test_rejects_blank_title(self, blank_title):
		with pytest.raises(EmptyTitle):
			factories.make_ticket(title=blank_title)

	@pytest.mark.parametrize("blank_description", ["", "   ", "\t\n"])
	def test_rejects_blank_description(self, blank_description):
		with pytest.raises(EmptyDescription):
			factories.make_ticket(description=blank_description)

	def test_rejects_non_uuid_assignee(self):
		# The domain guard only fires when assignee_id is not None, so a
		# non-UUID truthy value (e.g. a raw string id) must still be rejected.
		with pytest.raises(InvalidAssignee):
			Ticket.create(
				id=factories.new_uuid(),
				title="Title",
				description="Description",
				priority=Priority.LOW,
				created_at=factories.BASE_TIME,
				application=Application.APP_1,
				assignee_id="not-a-uuid",  # type: ignore[arg-type]
			)
