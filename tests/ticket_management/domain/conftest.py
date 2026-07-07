"""
Fixtures for domain-layer tests.

These wrap the plain factories in `factories.py` so tests can request a
ticket in a given lifecycle state (e.g. `resolved_ticket`) without
repeating the setup steps needed to reach that state. Each fixture builds
a brand-new entity per test, so tests can never leak state into one
another.
"""
from __future__ import annotations

import pytest

from tests.ticket_management.domain import factories


@pytest.fixture
def open_ticket():
	"""A freshly created, unassigned ticket in the OPEN status."""
	return factories.make_ticket()


@pytest.fixture
def assigned_ticket():
	"""An OPEN ticket that already has an assignee."""
	return factories.make_assigned_ticket()


@pytest.fixture
def in_progress_ticket():
	return factories.make_in_progress_ticket()


@pytest.fixture
def pending_ticket():
	return factories.make_pending_ticket()


@pytest.fixture
def resolved_ticket():
	return factories.make_resolved_ticket()


@pytest.fixture
def closed_ticket():
	return factories.make_closed_ticket()


@pytest.fixture
def archived_ticket():
	return factories.make_archived_ticket()


@pytest.fixture
def comment():
	return factories.make_comment()


@pytest.fixture
def attachment():
	return factories.make_attachment()
