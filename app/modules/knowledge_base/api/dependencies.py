from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from app.modules.knowledge_base.application.queries.get_similar_incidents.handler import GetSimilarIncidentsHandler
from app.modules.knowledge_base.infrastructure.persistence.repositories.sqlalchemy_similarity_read_repository import (
	SqlAlchemySimilarityReadRepository,
)
from app.modules.ticket_management.api.dependencies import get_read_repository as get_ticket_read_repository
from app.modules.ticket_management.infrastructure.persistence.repositories.sqlalchemy_ticket_read_repository import (
	SqlAlchemyTicketReadRepository,
)
from app.shared.database.session import create_session


async def get_similarity_read_repository() -> AsyncIterator[SqlAlchemySimilarityReadRepository]:
	session = create_session()
	try:
		yield SqlAlchemySimilarityReadRepository(session)
	finally:
		await session.close()


def get_get_similar_incidents_handler(
	similarity_read_repository: Annotated[SqlAlchemySimilarityReadRepository, Depends(get_similarity_read_repository)],
	ticket_read_repository: Annotated[SqlAlchemyTicketReadRepository, Depends(get_ticket_read_repository)],
) -> GetSimilarIncidentsHandler:
	return GetSimilarIncidentsHandler(similarity_read_repository, ticket_read_repository)
