from __future__ import annotations

from typing import Any
from uuid import UUID

from app.modules.ticket_management.application.dto.attachment_dto import AttachmentDTO
from app.modules.ticket_management.application.dto.comment_dto import CommentDTO
from app.modules.ticket_management.application.security.support import (
	TicketReadRepositoryScope,
	UserReadRepositoryScope,
	has_application_assignment,
	is_admin,
	parse_uuid,
)
from app.shared.security.authorization_result import AuthorizationResult
from app.shared.security.current_user import CurrentUser
from app.shared.security.instance_authorization_policy import InstanceAuthorizationPolicy


class AttachmentAccessPolicy(InstanceAuthorizationPolicy):
	def __init__(
		self,
		ticket_repository_scope: TicketReadRepositoryScope,
		user_repository_scope: UserReadRepositoryScope,
	) -> None:
		self._ticket_repository_scope = ticket_repository_scope
		self._user_repository_scope = user_repository_scope

	async def authorize(self, *, current_user: CurrentUser, resource_id: Any, operation: str) -> AuthorizationResult:
		# `resource_id` is not tied to "attachment" as a type: its meaning depends
		# on which path_param the route bound it to (see routes.py). For "create"
		# it is the parent ticket_id (no attachment exists yet); for "create_on_comment"
		# it is the parent comment_id (no attachment exists yet either); for "delete"
		# and "read" it is the attachment_id itself.
		if operation == "create":
			ticket_id = parse_uuid(resource_id)
			if ticket_id is None:
				return AuthorizationResult(False, "Invalid ticket identifier.")
			async with self._ticket_repository_scope() as tickets:
				ticket = await tickets.get_ticket(ticket_id)
			if ticket is None:
				# Let the request through: the handler will raise the proper
				# not-found error. A missing resource is not an authorization outcome.
				return AuthorizationResult(True, "")
			if ticket.assignee_id == current_user.id:
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "Only the ticket assignee can add attachments directly to the ticket.")

		if operation == "create_on_comment":
			comment_id = parse_uuid(resource_id)
			if comment_id is None:
				return AuthorizationResult(False, "Invalid comment identifier.")
			comment = await self._get_comment(comment_id)
			if comment is None:
				return AuthorizationResult(True, "")
			if comment.author_id == current_user.id:
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "Only the comment author can attach files to it.")

		if operation == "read":
			attachment_id = parse_uuid(resource_id)
			if attachment_id is None:
				return AuthorizationResult(False, "Invalid attachment identifier.")
			async with self._ticket_repository_scope() as tickets:
				ticket_id = await tickets.get_ticket_id_for_attachment(attachment_id)
				if ticket_id is None:
					return AuthorizationResult(True, "")
				ticket = await tickets.get_ticket(ticket_id)
			if ticket is None:
				return AuthorizationResult(True, "")
			if has_application_assignment(current_user, ticket.application) or await is_admin(self._user_repository_scope, current_user):
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "You are not authorized to access this attachment.")

		if operation == "delete":
			attachment_id = parse_uuid(resource_id)
			if attachment_id is None:
				return AuthorizationResult(False, "Invalid attachment identifier.")
			attachment = await self._get_attachment(attachment_id)
			if attachment is None:
				return AuthorizationResult(True, "")
			if attachment.uploaded_by == current_user.id:
				return AuthorizationResult(True, "")
			return AuthorizationResult(False, "Only the attachment uploader can delete it.")

		return AuthorizationResult(False, f"Unknown attachment operation '{operation}'.")

	async def _get_attachment(self, attachment_id: UUID) -> AttachmentDTO | None:
		async with self._ticket_repository_scope() as tickets:
			ticket_id = await tickets.get_ticket_id_for_attachment(attachment_id)
			if ticket_id is None:
				return None
			ticket = await tickets.get_ticket(ticket_id)
		if ticket is None:
			return None
		direct = next((attachment for attachment in ticket.attachments if attachment.id == attachment_id), None)
		if direct is not None:
			return direct
		for comment in ticket.comments:
			nested = next((attachment for attachment in comment.attachments if attachment.id == attachment_id), None)
			if nested is not None:
				return nested
		return None

	async def _get_comment(self, comment_id: UUID) -> CommentDTO | None:
		async with self._ticket_repository_scope() as tickets:
			ticket_id = await tickets.get_ticket_id_for_comment(comment_id)
			if ticket_id is None:
				return None
			ticket = await tickets.get_ticket(ticket_id)
		if ticket is None:
			return None
		return next((comment for comment in ticket.comments if comment.id == comment_id), None)
