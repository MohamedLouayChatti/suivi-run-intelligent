from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from app.modules.conversational_assistant.domain.repositories.conversation_repository import ConversationRepository


class UnitOfWork(ABC):
	conversations: ConversationRepository

	@abstractmethod
	async def commit(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def rollback(self) -> None:
		raise NotImplementedError

	@abstractmethod
	async def __aenter__(self) -> Self:
		raise NotImplementedError

	@abstractmethod
	async def __aexit__(
		self,
		exc_type: type[BaseException] | None,
		exc: BaseException | None,
		tb: TracebackType | None,
	) -> None:
		raise NotImplementedError
