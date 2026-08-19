from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from uuid import UUID

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.ticket_identity_key import TicketIdentityKey
from app.modules.ticket_management.application.dto.ticket_dto import (
	TicketContentDTO,
	TicketDetailDTO,
	TicketSimilaritySummaryDTO,
	TicketSummaryDTO,
)
from app.modules.ticket_management.application.queries.export_ticket_history.query import ExportTicketHistoryQuery
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery


class TicketReadRepository(ABC):
	@abstractmethod
	async def get_ticket(self, ticket_id: UUID) -> TicketDetailDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def list_tickets(self, query: ListTicketsQuery) -> list[TicketSummaryDTO]:
		raise NotImplementedError

	@abstractmethod
	async def search_tickets(self, query: SearchTicketsQuery) -> list[TicketSummaryDTO]:
		raise NotImplementedError

	@abstractmethod
	async def list_history_for_export(self, query: ExportTicketHistoryQuery) -> list[TicketSummaryDTO]:
		raise NotImplementedError

	@abstractmethod
	async def get_ticket_id_for_comment(self, comment_id: UUID) -> UUID | None:
		raise NotImplementedError

	@abstractmethod
	async def get_ticket_id_for_attachment(self, attachment_id: UUID) -> UUID | None:
		raise NotImplementedError

	@abstractmethod
	async def get_attachment(self, attachment_id: UUID) -> AttachmentDTO | None:
		raise NotImplementedError

	@abstractmethod
	async def get_similarity_summaries(self, ticket_ids: list[UUID]) -> list[TicketSimilaritySummaryDTO]:
		"""Batch projection consumed by Knowledge Base to enrich persisted SimilarityResult rows
		with live title/status/resolution_notes -- never cached on the Knowledge Base side."""
		raise NotImplementedError

	@abstractmethod
	async def list_ticket_contents(self, *, after_id: UUID | None, limit: int) -> list[TicketContentDTO]:
		"""One page of ticket text, ordered by id, for a bulk pass over the whole corpus.

		Keyset pagination (`id > after_id`) rather than LIMIT/OFFSET: a full pass takes long enough
		that rows can be inserted underneath it, and OFFSET would then silently skip or repeat
		tickets as earlier pages shift. Ordering by id is arbitrary but stable, which is all a
		complete traversal needs.

		Includes archived tickets. Archival is a soft delete in this module and does not retract
		what a ticket recorded, so excluding them here would make a bulk pass disagree with the
		per-ticket path, which sees every ticket at creation and never revisits it.
		"""
		raise NotImplementedError

	@abstractmethod
	async def find_existing_identity_keys(self, keys: Sequence[TicketIdentityKey]) -> set[TicketIdentityKey]:
		"""Which of `keys` already identify a stored ticket.

		Asked by the batch import before it writes anything, to refuse a file that repeats incidents
		already in the database -- re-uploading an export is the likeliest way an import goes wrong,
		and nothing in the schema would stop it: neither external identifier is unique, and both are
		legitimately absent on plenty of tickets.

		Returns the subset that matched rather than a per-key answer, because the caller has a set of
		candidates and one question about all of them, and because a key that matched several tickets
		is no different here from one that matched a single ticket.
		"""
		raise NotImplementedError
