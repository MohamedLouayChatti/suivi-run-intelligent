from __future__ import annotations

from typing import Any

from app.modules.conversational_assistant.application.security.support import (
	ConversationReadRepositoryScope,
	parse_uuid,
)
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy


class AgentRunAccessPolicy(InstanceAuthorizationPolicy):
	"""Same self-only posture as ConversationAccessPolicy, resolved through the run's owning
	conversation -- a run has no owner of its own, only the conversation it belongs to.
	"""

	def __init__(self, conversation_read_repository_scope: ConversationReadRepositoryScope) -> None:
		self._scope = conversation_read_repository_scope

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		run_id = parse_uuid(resource_id)
		if run_id is None:
			return AuthorizationResult(False, "Invalid run identifier.")

		async with self._scope() as conversations:
			owner_id = await conversations.get_run_owner(run_id)

		if owner_id is None:
			return AuthorizationResult(True, "")
		if owner_id == current_user.id:
			return AuthorizationResult(True, "")
		return AuthorizationResult(False, "You are not authorized to access this run.")
