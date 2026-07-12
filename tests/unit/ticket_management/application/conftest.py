"""
Shared fixtures for application-layer tests.

Every command handler takes the same two collaborators (`UnitOfWork`,
`EventPublisher`), so those are provided as fixtures here. Domain entity
construction is delegated to the domain layer's own factories
(`tests.ticket_management.domain.factories`) so ticket set-up logic isn't
duplicated between the two test suites.
"""
from __future__ import annotations

import pytest

from tests.unit.ticket_management.application.fakes import (
	FakeEventPublisher,
	FakeTicketReadRepository,
	FakeTicketRepository,
	FakeUnitOfWork,
)


@pytest.fixture
def ticket_repository() -> FakeTicketRepository:
	return FakeTicketRepository()


@pytest.fixture
def uow(ticket_repository: FakeTicketRepository) -> FakeUnitOfWork:
	return FakeUnitOfWork(tickets=ticket_repository)


@pytest.fixture
def event_publisher() -> FakeEventPublisher:
	return FakeEventPublisher()


@pytest.fixture
def read_repository() -> FakeTicketReadRepository:
	return FakeTicketReadRepository()
