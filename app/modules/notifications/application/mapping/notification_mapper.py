from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any
from uuid import UUID, uuid4

from app.modules.notifications.application.mapping.recipient_resolution import RecipientResolver
from app.modules.notifications.domain.entities.notification import Notification
from app.modules.notifications.domain.enums.notification_type import NotificationType
from app.modules.notifications.domain.value_objects.notification_action import (
	NotificationAction,
	OpenCommentAction,
	OpenTicketAction,
	OpenUserAction,
)
from app.shared.events.event import DomainEvent

from app.modules.ticket_management.domain.enums.functional_team import FunctionalTeam
from app.modules.ticket_management.domain.enums.transfer_destination import TransferDestination
from app.modules.ticket_management.domain.events.attachment_added import AttachmentAdded
from app.modules.ticket_management.domain.events.attachment_deleted import AttachmentDeleted
from app.modules.ticket_management.domain.events.comment_added import CommentAdded
from app.modules.ticket_management.domain.events.comment_deleted import CommentDeleted
from app.modules.ticket_management.domain.events.comment_edited import CommentEdited
from app.modules.ticket_management.domain.events.priority_changed import PriorityChanged
from app.modules.ticket_management.domain.events.ticket_archived import TicketArchived
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

# Only these 6 TransferDestination members correspond to a Ticket Management/Auth
# Application value -- the other 9 (EEP, CLIP, BANCO, ULYSSE, ACACIA, SANTAFE,
# PROXIMA, HABILITATION, DEVELOPMENT_TEAM) have no matching user application
# assignment anywhere in the system, so a transfer to one of them produces no
# notification. Confirmed with the user rather than guessed.
#
# FCI and COLORIS split into Support/Configuration teams, so a transfer to one of
# those must only reach users on the matching team -- otherwise Configuration
# engineers would be notified about tickets landing on the Support queue and vice
# versa. AERO and VIO have no such split (mirrors TransferDestination's own
# _ORIGIN_BY_DESTINATION in the ticket_management domain): any active user
# assigned to that application is a valid recipient regardless of team.
_TRANSFER_DESTINATION_TARGET: dict[TransferDestination, tuple[str, str | None]] = {
	TransferDestination.SUPPORT_FCI: ("FCI", FunctionalTeam.SUPPORT.value),
	TransferDestination.CONFIG_FCI: ("FCI", FunctionalTeam.CONFIGURATION.value),
	TransferDestination.SUPPORT_COLORIS: ("COLORIS", FunctionalTeam.SUPPORT.value),
	TransferDestination.CONFIG_COLORIS: ("COLORIS", FunctionalTeam.CONFIGURATION.value),
	TransferDestination.AERO: ("AERO", None),
	TransferDestination.VIO: ("VIO", None),
}


class NotificationMapper:
	"""Translates domain events published elsewhere in the system into Notification
	aggregates -- same registry philosophy as Audit's AuditMapper. Unlike AuditMapper,
	methods here are async and return a list: some events need a lookup to resolve
	who should be notified (the ticket's current assignee, or a broadcast set of
	users), and some events legitimately have zero or several recipients.

	The acting user is always excluded from the recipient list -- this is the single
	place "don't notify a user of their own action" is enforced, so no caller has to
	repeat that guard.
	"""

	def __init__(self, recipients: RecipientResolver) -> None:
		self._recipients = recipients
		self._mappings: dict[type[DomainEvent], Callable[[DomainEvent], Awaitable[list[Notification]]]] = {
			TicketReassigned: self._ticket_reassigned,
			PriorityChanged: self._priority_changed,
			TicketStatusChanged: self._ticket_status_changed,
			CommentAdded: self._comment_added,
			CommentEdited: self._comment_edited,
			CommentDeleted: self._comment_deleted,
			AttachmentAdded: self._attachment_added,
			AttachmentDeleted: self._attachment_deleted,
			TicketArchived: self._ticket_archived,
			TicketRestored: self._ticket_restored,
			TicketTransferred: self._ticket_transferred,
			UserActivated: self._user_activated,
			UserDeactivated: self._user_deactivated,
			RoleAssignedToUser: self._role_assigned,
			RoleRevokedFromUser: self._role_revoked,
			PermissionGrantedToUser: self._permission_granted,
			PermissionRevokedFromUser: self._permission_revoked,
			RolePermissionGranted: self._role_permission_granted,
			RolePermissionRevoked: self._role_permission_revoked,
			UserCreated: self._user_created,
		}

	async def to_notifications(self, event: DomainEvent) -> list[Notification]:
		mapping = self._mappings.get(type(event))
		if mapping is None:
			return []
		return await mapping(event)

	def _notification(
		self, event: DomainEvent, *, recipient_id: UUID, title: str, message: str,
		type: NotificationType, action: NotificationAction | None, metadata: dict[str, Any],
	) -> Notification:
		return Notification.create(
			id=uuid4(), recipient_id=recipient_id, title=title, message=message,
			type=type, action=action, created_at=event.occurred_at, metadata=metadata,
		)

	def _for_recipients(
		self, event: DomainEvent, recipient_ids: Iterable[UUID], *, title: str, message: str,
		type: NotificationType, action: NotificationAction | None, metadata: dict[str, Any],
	) -> list[Notification]:
		return [
			self._notification(event, recipient_id=recipient_id, title=title, message=message, type=type, action=action, metadata=metadata)
			for recipient_id in recipient_ids
			if recipient_id != event.actor_id
		]

	# -- Ticket Management ---------------------------------------------------

	async def _ticket_reassigned(self, event: TicketReassigned) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [event.assignee_id],
			title="Ticket reassigned to you", message=f'You were assigned to ticket "{ticket.title}".',
			type=NotificationType.TICKET_ASSIGNED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title},
		)

	async def _priority_changed(self, event: PriorityChanged) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Ticket priority changed",
			message=f'Priority for "{ticket.title}" changed from {event.old_priority.value} to {event.new_priority.value}.',
			type=NotificationType.TICKET_PRIORITY_CHANGED, action=OpenTicketAction(event.ticket_id),
			metadata={
				"ticket_id": str(event.ticket_id), "ticket_title": ticket.title,
				"old_priority": event.old_priority.value, "new_priority": event.new_priority.value,
			},
		)

	async def _ticket_status_changed(self, event: TicketStatusChanged) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Ticket status changed",
			message=f'Status for "{ticket.title}" changed from {event.old_status.value} to {event.new_status.value}.',
			type=NotificationType.TICKET_STATUS_CHANGED, action=OpenTicketAction(event.ticket_id),
			metadata={
				"ticket_id": str(event.ticket_id), "ticket_title": ticket.title,
				"old_status": event.old_status.value, "new_status": event.new_status.value,
			},
		)

	async def _comment_added(self, event: CommentAdded) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="New comment", message=f'A new comment was added to "{ticket.title}".',
			type=NotificationType.COMMENT_ADDED, action=OpenCommentAction(event.ticket_id, event.comment_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "comment_id": str(event.comment_id)},
		)

	async def _comment_edited(self, event: CommentEdited) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Comment edited", message=f'A comment on "{ticket.title}" was edited.',
			type=NotificationType.COMMENT_EDITED, action=OpenCommentAction(event.ticket_id, event.comment_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "comment_id": str(event.comment_id)},
		)

	async def _comment_deleted(self, event: CommentDeleted) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Comment deleted", message=f'A comment on "{ticket.title}" was deleted.',
			type=NotificationType.COMMENT_DELETED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "comment_id": str(event.comment_id)},
		)

	async def _attachment_added(self, event: AttachmentAdded) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="New attachment", message=f'A new attachment was added to "{ticket.title}".',
			type=NotificationType.ATTACHMENT_ADDED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "attachment_id": str(event.attachment_id)},
		)

	async def _attachment_deleted(self, event: AttachmentDeleted) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Attachment deleted", message=f'An attachment on "{ticket.title}" was deleted.',
			type=NotificationType.ATTACHMENT_DELETED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "attachment_id": str(event.attachment_id)},
		)

	async def _ticket_archived(self, event: TicketArchived) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Ticket archived", message=f'"{ticket.title}" was archived.',
			type=NotificationType.TICKET_ARCHIVED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title},
		)

	async def _ticket_restored(self, event: TicketRestored) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Ticket restored", message=f'"{ticket.title}" was restored.',
			type=NotificationType.TICKET_RESTORED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title},
		)

	async def _ticket_transferred(self, event: TicketTransferred) -> list[Notification]:
		target = _TRANSFER_DESTINATION_TARGET.get(event.transferred_to)
		if target is None:
			return []
		application_value, functional_team_value = target
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		recipient_ids = await self._recipients.active_user_ids_with_application(application_value, functional_team_value)
		return self._for_recipients(
			event, recipient_ids,
			title="Ticket transferred to your team", message=f'"{ticket.title}" was transferred to {event.transferred_to.value}.',
			type=NotificationType.TICKET_TRANSFERRED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "transferred_to": event.transferred_to.value},
		)

	# -- Auth ------------------------------------------------------------------

	async def _user_activated(self, event: UserActivated) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Account activated", message="Your account was activated.",
			type=NotificationType.ACCOUNT_ACTIVATED, action=None,
			metadata={"user_id": str(event.user_id)},
		)

	async def _user_deactivated(self, event: UserDeactivated) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Account deactivated", message="Your account was deactivated.",
			type=NotificationType.ACCOUNT_DEACTIVATED, action=None,
			metadata={"user_id": str(event.user_id)},
		)

	async def _role_assigned(self, event: RoleAssignedToUser) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Role assigned", message=f"You were assigned the role {event.role_id}.",
			type=NotificationType.ROLE_ASSIGNED, action=None,
			metadata={"user_id": str(event.user_id), "role_id": str(event.role_id)},
		)

	async def _role_revoked(self, event: RoleRevokedFromUser) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Role revoked", message=f"The role {event.role_id} was revoked from your account.",
			type=NotificationType.ROLE_REVOKED, action=None,
			metadata={"user_id": str(event.user_id), "role_id": str(event.role_id)},
		)

	async def _permission_granted(self, event: PermissionGrantedToUser) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Permission granted", message=f"You were granted the permission {event.permission_id}.",
			type=NotificationType.PERMISSION_GRANTED, action=None,
			metadata={"user_id": str(event.user_id), "permission_id": str(event.permission_id)},
		)

	async def _permission_revoked(self, event: PermissionRevokedFromUser) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Permission revoked", message=f"The permission {event.permission_id} was revoked from your account.",
			type=NotificationType.PERMISSION_REVOKED, action=None,
			metadata={"user_id": str(event.user_id), "permission_id": str(event.permission_id)},
		)

	async def _role_permission_granted(self, event: RolePermissionGranted) -> list[Notification]:
		recipient_ids = await self._recipients.active_user_ids_with_role(event.role_id)
		return self._for_recipients(
			event, recipient_ids,
			title="Role permissions changed", message=f"The permission {event.permission_id} was granted to the role {event.role_id}.",
			type=NotificationType.ROLE_PERMISSION_GRANTED, action=None,
			metadata={"role_id": str(event.role_id), "permission_id": str(event.permission_id)},
		)

	async def _role_permission_revoked(self, event: RolePermissionRevoked) -> list[Notification]:
		recipient_ids = await self._recipients.active_user_ids_with_role(event.role_id)
		return self._for_recipients(
			event, recipient_ids,
			title="Role permissions changed", message=f"The permission {event.permission_id} was revoked from the role {event.role_id}.",
			type=NotificationType.ROLE_PERMISSION_REVOKED, action=None,
			metadata={"role_id": str(event.role_id), "permission_id": str(event.permission_id)},
		)

	async def _user_created(self, event: UserCreated) -> list[Notification]:
		welcome = self._for_recipients(
			event, [event.user_id],
			title="Welcome", message=f"Welcome, {event.display_name}! Your account has been created.",
			type=NotificationType.ACCOUNT_CREATED, action=None,
			metadata={"user_id": str(event.user_id)},
		)
		admin_ids = await self._recipients.active_admin_user_ids()
		admin_ids = admin_ids - {event.user_id}
		announcements = self._for_recipients(
			event, admin_ids,
			title="New user registered", message=f"{event.display_name} ({event.email}) just joined.",
			type=NotificationType.NEW_USER_REGISTERED, action=OpenUserAction(event.user_id),
			metadata={"user_id": str(event.user_id), "email": event.email, "display_name": event.display_name},
		)
		return welcome + announcements
