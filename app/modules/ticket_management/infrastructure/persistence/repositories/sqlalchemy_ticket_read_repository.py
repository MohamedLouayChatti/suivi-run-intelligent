from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, time
from uuid import UUID

from sqlalchemy import ColumnElement, Select, String, and_, cast, func, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.ticket_dto import (
	TicketContentDTO,
	TicketDetailDTO,
	TicketSimilaritySummaryDTO,
	TicketSummaryDTO,
)
from app.modules.ticket_management.application.dto.ticket_identity_key import TicketIdentityKey
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.export_ticket_history.query import ExportTicketHistoryQuery
from app.modules.ticket_management.application.queries.list_ticket_history.query import ListTicketHistoryQuery
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.domain.enums.status import Status
from app.modules.ticket_management.infrastructure.persistence import mapper
from app.modules.ticket_management.infrastructure.persistence.models.attachment_model import AttachmentModel
from app.modules.ticket_management.infrastructure.persistence.models.comment_model import CommentModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel

ACTIVE_STATUSES = (Status.OPEN, Status.IN_PROGRESS, Status.RESOLVED)
COMPLETED_STATUSES = (Status.CLOSED, Status.TRANSFERRED)

# Postgres has to compare stored tickets the same way the application normalizes the candidate keys
# it is asking about, so this is the SQL counterpart of `normalize_identity_text` and the two only
# mean anything as a pair: collapse runs of whitespace, trim the ends, lower-case, and read a NULL
# identifier as the empty string an absent CSV cell becomes. `lower()` rather than a case-folding
# collation for exactly that reason -- it is the operation the Python side was written to match.
# The comparison is deliberately computed rather than indexed: it runs once per import over a
# corpus of a few thousand rows, and an expression index maintained on every ticket write would
# cost far more than the scan it saves.
_KEY_BATCH_SIZE = 500


def _normalized(column: ColumnElement[str | None]) -> ColumnElement[str]:
	return func.lower(func.btrim(func.regexp_replace(func.coalesce(column, ""), r"\s+", " ", "g")))


class SqlAlchemyTicketReadRepository(TicketReadRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def get_ticket(self, ticket_id: UUID) -> TicketDetailDTO | None:
		stmt = (
			select(TicketModel)
			.where(TicketModel.id == ticket_id)
			.options(
				selectinload(TicketModel.attachments),
				selectinload(TicketModel.comments).selectinload(CommentModel.attachments),
				selectinload(TicketModel.history),
			)
		)
		ticket_model = await self.session.scalar(stmt)
		if ticket_model is None:
			return None
		return mapper.ticket_model_to_detail_dto(ticket_model)

	async def list_tickets(self, query: ListTicketsQuery) -> list[TicketSummaryDTO]:
		stmt = self._build_list_query(query)
		result = await self.session.scalars(stmt)
		return [mapper.ticket_model_to_summary_dto(ticket_model) for ticket_model in result.all()]

	async def count_tickets(self, query: ListTicketsQuery) -> int:
		stmt = self._apply_list_conditions(select(func.count(TicketModel.id)), query)
		return await self.session.scalar(stmt) or 0

	async def search_tickets(self, query: SearchTicketsQuery) -> list[TicketSummaryDTO]:
		stmt = self._build_search_query(query)
		result = await self.session.scalars(stmt)
		return [mapper.ticket_model_to_summary_dto(ticket_model) for ticket_model in result.all()]

	async def list_history_for_export(self, query: ExportTicketHistoryQuery) -> list[TicketSummaryDTO]:
		stmt = self._build_export_query(query)
		result = await self.session.scalars(stmt)
		return [mapper.ticket_model_to_summary_dto(ticket_model) for ticket_model in result.all()]

	async def list_history(self, query: ListTicketHistoryQuery) -> list[TicketSummaryDTO]:
		stmt = self._build_history_list_query(query)
		result = await self.session.scalars(stmt)
		return [mapper.ticket_model_to_summary_dto(ticket_model) for ticket_model in result.all()]

	async def count_history(self, query: ListTicketHistoryQuery) -> int:
		stmt = self._build_history_count_query(query)
		return await self.session.scalar(stmt) or 0

	async def get_ticket_id_for_comment(self, comment_id: UUID) -> UUID | None:
		return await self.session.scalar(select(CommentModel.ticket_id).where(CommentModel.id == comment_id))

	async def get_ticket_id_for_attachment(self, attachment_id: UUID) -> UUID | None:
		row = (
			await self.session.execute(
				select(AttachmentModel.ticket_id, AttachmentModel.comment_id).where(AttachmentModel.id == attachment_id)
			)
		).first()
		if row is None:
			return None
		ticket_id, comment_id = row
		if ticket_id is not None:
			return ticket_id
		return await self.get_ticket_id_for_comment(comment_id)

	async def get_attachment(self, attachment_id: UUID) -> AttachmentDTO | None:
		attachment_model = await self.session.scalar(select(AttachmentModel).where(AttachmentModel.id == attachment_id))
		if attachment_model is None:
			return None
		return mapper.attachment_model_to_dto(attachment_model)

	async def get_similarity_summaries(self, ticket_ids: list[UUID]) -> list[TicketSimilaritySummaryDTO]:
		if not ticket_ids:
			return []
		stmt = select(TicketModel).where(TicketModel.id.in_(ticket_ids))
		result = await self.session.scalars(stmt)
		return [
			TicketSimilaritySummaryDTO(id=m.id, title=m.title, status=m.status, resolution_notes=m.resolution_notes)
			for m in result.all()
		]

	async def list_ticket_contents(self, *, after_id: UUID | None, limit: int) -> list[TicketContentDTO]:
		# Selects columns rather than entities: a full-corpus pass has no use for the aggregate,
		# and loading TicketModel would drag its relationships along behind it.
		stmt = (
			select(
				TicketModel.id, TicketModel.application, TicketModel.description,
				TicketModel.genergy_id, TicketModel.oceane_id,
			)
			.order_by(TicketModel.id)
			.limit(limit)
		)
		if after_id is not None:
			stmt = stmt.where(TicketModel.id > after_id)
		rows = (await self.session.execute(stmt)).all()
		return [
			TicketContentDTO(
				id=row.id, application=row.application, description=row.description,
				genergy_id=row.genergy_id, oceane_id=row.oceane_id,
			)
			for row in rows
		]

	def _apply_list_conditions(self, stmt: Select[tuple], query: ListTicketsQuery) -> Select[tuple]:
		stmt = self._apply_common_filters(stmt, query.application, query.status, query.priority, query.assignee_id, query.functional_team, query.category, query.operational_highlight, query.include_archived, query.allowed_applications, created_from=query.created_from, created_to=query.created_to)
		if query.exclude_assignee_id is not None:
			stmt = stmt.where(TicketModel.assignee_id != query.exclude_assignee_id)
		if query.status is None and query.active_only:
			stmt = stmt.where(TicketModel.status.in_(ACTIVE_STATUSES))
		if query.search.strip():
			pattern = f"%{query.search.strip()}%"
			stmt = stmt.where(or_(TicketModel.title.ilike(pattern), cast(TicketModel.id, String).ilike(pattern)))
		return stmt

	def _build_list_query(self, query: ListTicketsQuery) -> Select[tuple[TicketModel]]:
		stmt = self._apply_list_conditions(select(TicketModel), query)
		return stmt.order_by(TicketModel.created_at.desc(), TicketModel.updated_at.desc()).limit(query.limit).offset(query.offset)

	def _build_search_query(self, query: SearchTicketsQuery) -> Select[tuple[TicketModel]]:
		stmt = select(TicketModel)
		stmt = self._apply_common_filters(stmt, query.application, query.status, query.priority, query.assignee_id, query.functional_team, query.category, query.operational_highlight, query.include_archived, query.allowed_applications, created_from=query.created_from, created_to=query.created_to)
		pattern = f"%{query.term}%"
		stmt = stmt.where(or_(TicketModel.title.ilike(pattern), TicketModel.description.ilike(pattern)))
		return stmt.order_by(TicketModel.created_at.desc(), TicketModel.updated_at.desc()).limit(query.limit).offset(query.offset)

	def _apply_history_conditions(self, stmt: Select[tuple], *, application, status, category, assignee_id, search: str, date_from, date_to, allowed_applications) -> Select[tuple]:
		"""Shared by the CSV export and the on-screen history list -- both mean "completed
		tickets matching these filters," they differ only in whether the result is bounded."""
		stmt = self._apply_common_filters(stmt, application, None, None, assignee_id, None, category, None, False, allowed_applications)
		statuses = (status,) if status is not None else COMPLETED_STATUSES
		stmt = stmt.where(TicketModel.status.in_(statuses))
		if search.strip():
			pattern = f"%{search.strip()}%"
			stmt = stmt.where(or_(TicketModel.title.ilike(pattern), cast(TicketModel.id, String).ilike(pattern)))
		if date_from is not None:
			stmt = stmt.where(TicketModel.updated_at >= datetime.combine(date_from, time.min, tzinfo=UTC))
		if date_to is not None:
			stmt = stmt.where(TicketModel.updated_at <= datetime.combine(date_to, time.max, tzinfo=UTC))
		return stmt

	def _build_export_query(self, query: ExportTicketHistoryQuery) -> Select[tuple[TicketModel]]:
		stmt = self._apply_history_conditions(
			select(TicketModel), application=query.application, status=query.status, category=query.category,
			assignee_id=query.assignee_id, search=query.search, date_from=query.date_from, date_to=query.date_to,
			allowed_applications=query.allowed_applications,
		)
		return stmt.order_by(TicketModel.updated_at.desc())

	def _build_history_list_query(self, query: ListTicketHistoryQuery) -> Select[tuple[TicketModel]]:
		stmt = self._apply_history_conditions(
			select(TicketModel), application=query.application, status=query.status, category=query.category,
			assignee_id=query.assignee_id, search=query.search, date_from=query.date_from, date_to=query.date_to,
			allowed_applications=query.allowed_applications,
		)
		return stmt.order_by(TicketModel.updated_at.desc()).limit(query.limit).offset(query.offset)

	def _build_history_count_query(self, query: ListTicketHistoryQuery) -> Select[tuple[int]]:
		return self._apply_history_conditions(
			select(func.count(TicketModel.id)), application=query.application, status=query.status,
			category=query.category, assignee_id=query.assignee_id, search=query.search,
			date_from=query.date_from, date_to=query.date_to, allowed_applications=query.allowed_applications,
		)

	def _apply_common_filters(self, stmt: Select[tuple[TicketModel]], application, status, priority, assignee_id, functional_team, category, operational_highlight, include_archived: bool, allowed_applications=None, *, created_from=None, created_to=None) -> Select[tuple[TicketModel]]:
		conditions = []
		# Keyword-only and last, so the history conditions -- which bound `updated_at` instead and
		# pass everything else positionally -- are unaffected by their arrival.
		if created_from is not None:
			conditions.append(TicketModel.created_at >= datetime.combine(created_from, time.min, tzinfo=UTC))
		if created_to is not None:
			conditions.append(TicketModel.created_at <= datetime.combine(created_to, time.max, tzinfo=UTC))
		if application is not None:
			conditions.append(TicketModel.application == application)
		if status is not None:
			conditions.append(TicketModel.status == status)
		if priority is not None:
			conditions.append(TicketModel.priority == priority)
		if assignee_id is not None:
			conditions.append(TicketModel.assignee_id == assignee_id)
		if functional_team is not None:
			conditions.append(TicketModel.functional_team == functional_team)
		if category is not None:
			conditions.append(TicketModel.category == category)
		if operational_highlight is not None:
			conditions.append(TicketModel.operational_highlight == operational_highlight)
		if not include_archived:
			conditions.append(TicketModel.archived_at.is_(None))
		if allowed_applications is not None:
			conditions.append(TicketModel.application.in_(allowed_applications))
		if conditions:
			stmt = stmt.where(and_(*conditions))
		return stmt

	async def find_existing_identity_keys(self, keys: Sequence[TicketIdentityKey]) -> set[TicketIdentityKey]:
		if not keys:
			return set()

		candidate = tuple_(
			_normalized(TicketModel.genergy_id),
			_normalized(TicketModel.oceane_id),
			_normalized(TicketModel.description),
		)
		unique = list({key for key in keys})
		found: set[TicketIdentityKey] = set()
		# Chunked because a file may carry thousands of rows and each key spends three bind parameters;
		# one statement per few hundred keys stays comfortably clear of the parameter ceiling without
		# turning the check into a query per row.
		for start in range(0, len(unique), _KEY_BATCH_SIZE):
			batch = unique[start : start + _KEY_BATCH_SIZE]
			stmt = select(
				_normalized(TicketModel.genergy_id),
				_normalized(TicketModel.oceane_id),
				_normalized(TicketModel.description),
			).where(
				candidate.in_([(key.genergy_id, key.oceane_id, key.description) for key in batch])
			)
			for row in (await self.session.execute(stmt)).all():
				found.add(TicketIdentityKey(genergy_id=row[0], oceane_id=row[1], description=row[2]))
		return found
