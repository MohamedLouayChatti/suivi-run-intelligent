from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.ticket_management.domain.entities.ticket import Ticket
from app.modules.ticket_management.domain.repositories.ticket_repository import TicketRepository
from app.modules.ticket_management.infrastructure.persistence import mapper
from app.modules.ticket_management.infrastructure.persistence.models.comment_model import CommentModel
from app.modules.ticket_management.infrastructure.persistence.models.ticket_model import TicketModel


class SqlAlchemyTicketRepository(TicketRepository):
	def __init__(self, session: AsyncSession) -> None:
		self.session = session

	async def add(self, ticket: Ticket) -> None:
		self.session.add(mapper.ticket_to_model(ticket))

	async def get(self, ticket_id: UUID) -> Ticket | None:
		ticket_model = await self._load_ticket_model(ticket_id)
		if ticket_model is None:
			return None
		return mapper.ticket_model_to_domain(ticket_model)

	async def save(self, ticket: Ticket) -> None:
		ticket_model = await self._load_ticket_model(ticket.id)
		if ticket_model is None:
			self.session.add(mapper.ticket_to_model(ticket))
			return
		mapper.sync_ticket_model(ticket_model, ticket)

	async def delete(self, ticket_id: UUID) -> None:
		ticket_model = await self._load_ticket_model(ticket_id)
		if ticket_model is not None:
			await self.session.delete(ticket_model)

	async def _load_ticket_model(self, ticket_id: UUID) -> TicketModel | None:
		stmt = (
			select(TicketModel)
			.where(TicketModel.id == ticket_id)
			.options(
				selectinload(TicketModel.attachments),
				selectinload(TicketModel.comments).selectinload(CommentModel.attachments),
			)
		)
		return await self.session.scalar(stmt)

