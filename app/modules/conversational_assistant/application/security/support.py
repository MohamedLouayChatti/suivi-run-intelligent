from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from uuid import UUID

from app.modules.conversational_assistant.application.interfaces.conversation_read_repository import (
	ConversationReadRepository,
)

ConversationReadRepositoryScope = Callable[[], AbstractAsyncContextManager[ConversationReadRepository]]


def parse_uuid(value: object) -> UUID | None:
	if isinstance(value, UUID):
		return value
	try:
		return UUID(str(value))
	except (TypeError, ValueError):
		return None
