from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from app.modules.audit.domain.entities.audit_entry import AuditEntry
from app.shared.events.event import DomainEvent

from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded
from app.modules.ticket_management.domain.events.attachment_deleted import AttachmentDeleted
from app.modules.ticket_management.domain.events.comment_added import CommentAdded
from app.modules.ticket_management.domain.events.comment_deleted import CommentDeleted
from app.modules.ticket_management.domain.events.comment_edited import CommentEdited
from app.modules.ticket_management.domain.events.jira_details_updated import JiraDetailsUpdated
from app.modules.ticket_management.domain.events.operational_highlight_changed import OperationalHighlightChanged
from app.modules.ticket_management.domain.events.priority_changed import PriorityChanged
from app.modules.ticket_management.domain.events.ticket_archived import TicketArchived
from app.modules.ticket_management.domain.events.ticket_created import TicketCreated
from app.modules.ticket_management.domain.events.ticket_reassigned import TicketReassigned
from app.modules.ticket_management.domain.events.ticket_restored import TicketRestored
from app.modules.ticket_management.domain.events.ticket_status_changed import TicketStatusChanged
from app.modules.ticket_management.domain.events.ticket_transferred import TicketTransferred

from app.modules.auth.domain.events.permission_granted_to_user import PermissionGrantedToUser
from app.modules.auth.domain.events.permission_revoked_from_user import PermissionRevokedFromUser
from app.modules.auth.domain.events.role_assigned_to_user import RoleAssignedToUser
from app.modules.auth.domain.events.role_permission_granted import RolePermissionGranted
from app.modules.auth.domain.events.role_permission_revoked import RolePermissionRevoked
from app.modules.auth.domain.events.role_revoked_from_user import RoleRevokedFromUser
from app.modules.auth.domain.events.user_activated import UserActivated
from app.modules.auth.domain.events.user_created import UserCreated
from app.modules.auth.domain.events.user_deactivated import UserDeactivated
from app.modules.auth.domain.events.user_updated import UserUpdated


class AuditMapper:
	"""Translates domain events published elsewhere in the system into AuditEntry records.

	Adding a new event type means adding one `_mappings` entry and one small
	translation method below -- nothing else in the audit module changes.

	occurred_at/actor_id are read uniformly from the DomainEvent envelope (see
	app/shared/events/event.py) for every event type here -- no more per-event-type
	timestamp-field-name or actor special-casing.
	"""

	def __init__(self) -> None:
		self._mappings: dict[type[DomainEvent], Callable[[DomainEvent], AuditEntry]] = {
			TicketCreated: self._ticket_created,
			TicketStatusChanged: self._ticket_status_changed,
			TicketReassigned: self._ticket_reassigned,
			PriorityChanged: self._priority_changed,
			TicketTransferred: self._ticket_transferred,
			CommentAdded: self._comment_added,
			CommentEdited: self._comment_edited,
			CommentDeleted: self._comment_deleted,
			AttachmentAdded: self._attachment_added,
			AttachmentDeleted: self._attachment_deleted,
			TicketArchived: self._ticket_archived,
			TicketRestored: self._ticket_restored,
			JiraDetailsUpdated: self._jira_details_updated,
			OperationalHighlightChanged: self._operational_highlight_changed,
			UserCreated: self._user_created,
			UserUpdated: self._user_updated,
			UserActivated: self._user_activated,
			UserDeactivated: self._user_deactivated,
			RoleAssignedToUser: self._role_assigned_to_user,
			RoleRevokedFromUser: self._role_revoked_from_user,
			PermissionGrantedToUser: self._permission_granted_to_user,
			PermissionRevokedFromUser: self._permission_revoked_from_user,
			RolePermissionGranted: self._role_permission_granted,
			RolePermissionRevoked: self._role_permission_revoked,
		}

	def to_entry(self, event: DomainEvent) -> AuditEntry | None:
		mapping = self._mappings.get(type(event))
		if mapping is None:
			return None
		return mapping(event)

	def _entry(self, event: DomainEvent, *, module: str, event_type: str, action: str, resource_type: str | None, payload: dict[str, Any]) -> AuditEntry:
		return AuditEntry.create(
			id=uuid4(),
			occurred_at=event.occurred_at,
			module=module,
			event_type=event_type,
			action=action,
			resource_type=resource_type,
			actor_id=event.actor_id,
			payload=payload,
		)

	# -- Ticket Management -------------------------------------------------

	def _ticket_created(self, event: TicketCreated) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="TicketCreated",
			action="ticket.created", resource_type="ticket",
			payload={
				"ticket_id": str(event.ticket_id), "title": event.title, "status": event.status.value,
				"priority": event.priority.value, "assignee_id": str(event.assignee_id),
				"category": event.category.value, "functional_team": event.functional_team.value,
			},
		)

	def _ticket_status_changed(self, event: TicketStatusChanged) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="TicketStatusChanged",
			action="ticket.status_changed", resource_type="ticket",
			payload={"ticket_id": str(event.ticket_id), "old_status": event.old_status.value, "new_status": event.new_status.value},
		)

	def _ticket_reassigned(self, event: TicketReassigned) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="TicketReassigned",
			action="ticket.reassigned", resource_type="ticket",
			payload={"ticket_id": str(event.ticket_id), "assignee_id": str(event.assignee_id)},
		)

	def _priority_changed(self, event: PriorityChanged) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="PriorityChanged",
			action="ticket.priority_changed", resource_type="ticket",
			payload={"ticket_id": str(event.ticket_id), "old_priority": event.old_priority.value, "new_priority": event.new_priority.value},
		)

	def _ticket_transferred(self, event: TicketTransferred) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="TicketTransferred",
			action="ticket.transferred", resource_type="ticket",
			payload={"ticket_id": str(event.ticket_id), "transferred_to": event.transferred_to.value},
		)

	def _comment_added(self, event: CommentAdded) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="CommentAdded",
			action="comment.added", resource_type="comment",
			payload={"ticket_id": str(event.ticket_id), "comment_id": str(event.comment_id), "author_id": str(event.author_id)},
		)

	def _comment_edited(self, event: CommentEdited) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="CommentEdited",
			action="comment.edited", resource_type="comment",
			payload={"ticket_id": str(event.ticket_id), "comment_id": str(event.comment_id)},
		)

	def _comment_deleted(self, event: CommentDeleted) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="CommentDeleted",
			action="comment.deleted", resource_type="comment",
			payload={"ticket_id": str(event.ticket_id), "comment_id": str(event.comment_id)},
		)

	def _attachment_added(self, event: AttachmentAdded) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="AttachmentAdded",
			action="attachment.added", resource_type="attachment",
			payload={"ticket_id": str(event.ticket_id), "attachment_id": str(event.attachment_id)},
		)

	def _attachment_deleted(self, event: AttachmentDeleted) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="AttachmentDeleted",
			action="attachment.deleted", resource_type="attachment",
			payload={"ticket_id": str(event.ticket_id), "attachment_id": str(event.attachment_id)},
		)

	def _ticket_archived(self, event: TicketArchived) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="TicketArchived",
			action="ticket.archived", resource_type="ticket",
			payload={"ticket_id": str(event.ticket_id)},
		)

	def _ticket_restored(self, event: TicketRestored) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="TicketRestored",
			action="ticket.restored", resource_type="ticket",
			payload={"ticket_id": str(event.ticket_id)},
		)

	def _jira_details_updated(self, event: JiraDetailsUpdated) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="JiraDetailsUpdated",
			action="ticket.jira_details_updated", resource_type="ticket",
			payload={
				"ticket_id": str(event.ticket_id), "requires_jira": event.requires_jira,
				"jira_id": event.jira_id, "jira_delivery_date": event.jira_delivery_date.isoformat() if event.jira_delivery_date else None,
			},
		)

	def _operational_highlight_changed(self, event: OperationalHighlightChanged) -> AuditEntry:
		return self._entry(
			event, module="ticket_management", event_type="OperationalHighlightChanged",
			action="ticket.operational_highlight_changed", resource_type="ticket",
			payload={"ticket_id": str(event.ticket_id), "operational_highlight": event.operational_highlight},
		)

	# -- Auth ----------------------------------------------------------------

	def _user_created(self, event: UserCreated) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="UserCreated",
			action="user.created", resource_type="user",
			payload={
				"user_id": str(event.user_id), "auth_provider_user_id": event.auth_provider_user_id.value,
				"email": event.email, "display_name": event.display_name, "functional_team": event.functional_team.value,
			},
		)

	def _user_updated(self, event: UserUpdated) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="UserUpdated",
			action="user.updated", resource_type="user",
			payload={"user_id": str(event.user_id)},
		)

	def _user_activated(self, event: UserActivated) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="UserActivated",
			action="user.activated", resource_type="user",
			payload={"user_id": str(event.user_id)},
		)

	def _user_deactivated(self, event: UserDeactivated) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="UserDeactivated",
			action="user.deactivated", resource_type="user",
			payload={"user_id": str(event.user_id)},
		)

	def _role_assigned_to_user(self, event: RoleAssignedToUser) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="RoleAssignedToUser",
			action="user.role_assigned", resource_type="user",
			payload={"user_id": str(event.user_id), "role_id": str(event.role_id)},
		)

	def _role_revoked_from_user(self, event: RoleRevokedFromUser) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="RoleRevokedFromUser",
			action="user.role_revoked", resource_type="user",
			payload={"user_id": str(event.user_id), "role_id": str(event.role_id)},
		)

	def _permission_granted_to_user(self, event: PermissionGrantedToUser) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="PermissionGrantedToUser",
			action="user.permission_granted", resource_type="user",
			payload={"user_id": str(event.user_id), "permission_id": str(event.permission_id)},
		)

	def _permission_revoked_from_user(self, event: PermissionRevokedFromUser) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="PermissionRevokedFromUser",
			action="user.permission_revoked", resource_type="user",
			payload={"user_id": str(event.user_id), "permission_id": str(event.permission_id)},
		)

	def _role_permission_granted(self, event: RolePermissionGranted) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="RolePermissionGranted",
			action="role.permission_granted", resource_type="role",
			payload={"role_id": str(event.role_id), "permission_id": str(event.permission_id)},
		)

	def _role_permission_revoked(self, event: RolePermissionRevoked) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="RolePermissionRevoked",
			action="role.permission_revoked", resource_type="role",
			payload={"role_id": str(event.role_id), "permission_id": str(event.permission_id)},
		)
