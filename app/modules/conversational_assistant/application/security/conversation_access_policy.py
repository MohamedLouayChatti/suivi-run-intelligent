from __future__ import annotations

from typing import Any

from app.modules.conversational_assistant.application.security.support import (
	ConversationReadRepositoryScope,
	parse_uuid,
)
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy


class ConversationAccessPolicy(InstanceAuthorizationPolicy):
	"""Strictly self-only: a conversation belongs to exactly one user, with no breadth
	override in v1 -- the same posture as the personal analytics endpoints, expressed as an
	instance policy here because a route names one conversation_id rather than a collection.
	"""

	def __init__(self, conversation_read_repository_scope: ConversationReadRepositoryScope) -> None:
		self._scope = conversation_read_repository_scope

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		conversation_id = parse_uuid(resource_id)
		if conversation_id is None:
			return AuthorizationResult(False, "Invalid conversation identifier.")

		async with self._scope() as conversations:
			owner_id = await conversations.get_owner(conversation_id)

		if owner_id is None:
			# Let the request through: the handler will raise the proper not-found error. A
			# missing resource is not an authorization outcome.
			return AuthorizationResult(True, "")
		if owner_id == current_user.id:
			return AuthorizationResult(True, "")
		return AuthorizationResult(False, "You are not authorized to access this conversation.")
