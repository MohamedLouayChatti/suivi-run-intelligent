from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.ticket_management.application.dto.ticket_dto import TicketDetailDTO, TicketSummaryDTO
from app.modules.ticket_management.application.interfaces.ticket_read_repository import TicketReadRepository
from app.modules.ticket_management.application.queries.list_tickets.query import ListTicketsQuery
from app.modules.ticket_management.application.queries.search_tickets.query import SearchTicketsQuery
from app.modules.ticket_management.infrastructure.persistence import mapper
from app.modules.ticket_management.infrastructure.persistence.models.attachment_model import AttachmentModel
from app.modules.ticket_management.infrastructure.persistence.models.comment_model import CommentModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel


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

	async def search_tickets(self, query: SearchTicketsQuery) -> list[TicketSummaryDTO]:
		stmt = self._build_search_query(query)
		result = await self.session.scalars(stmt)
		return [mapper.ticket_model_to_summary_dto(ticket_model) for ticket_model in result.all()]

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

	def _build_list_query(self, query: ListTicketsQuery) -> Select[tuple[TicketModel]]:
		stmt = select(TicketModel)
		stmt = self._apply_common_filters(stmt, query.application, query.status, query.priority, query.assignee_id, query.functional_team, query.category, query.operational_highlight, query.include_archived, query.allowed_applications)
		return stmt.order_by(TicketModel.created_at.desc(), TicketModel.updated_at.desc()).limit(query.limit).offset(query.offset)

	def _build_search_query(self, query: SearchTicketsQuery) -> Select[tuple[TicketModel]]:
		stmt = select(TicketModel)
		stmt = self._apply_common_filters(stmt, query.application, query.status, query.priority, query.assignee_id, query.functional_team, query.category, query.operational_highlight, query.include_archived, query.allowed_applications)
		pattern = f"%{query.term}%"
		stmt = stmt.where(or_(TicketModel.title.ilike(pattern), TicketModel.description.ilike(pattern)))
		return stmt.order_by(TicketModel.created_at.desc(), TicketModel.updated_at.desc()).limit(query.limit).offset(query.offset)

	def _apply_common_filters(self, stmt: Select[tuple[TicketModel]], application, status, priority, assignee_id, functional_team, category, operational_highlight, include_archived: bool, allowed_applications=None) -> Select[tuple[TicketModel]]:
		conditions = []
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

