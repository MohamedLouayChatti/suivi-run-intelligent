from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any
from uuid import UUID, uuid4

from app.modules.auth.application.dto.permission_dto import PermissionDTO
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
from app.modules.ticket_management.domain.enums.status import Status
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
from app.modules.auth.domain.enums.assignment_type import AssignmentType
from app.modules.auth.domain.enums.functional_team import FunctionalTeam as AuthFunctionalTeam
from app.modules.auth.domain.value_objects.application_assignment import ApplicationAssignment
from app.modules.auth.domain.events.user_organizational_identity_changed import (
	UserOrganizationalIdentityChanged,
)
from app.modules.auth.domain.events.user_role_changed import UserRoleChanged
from app.modules.auth.domain.events.role_permission_granted import RolePermissionGranted
from app.modules.auth.domain.events.role_permission_revoked import RolePermissionRevoked
from app.modules.auth.domain.events.user_activated import UserActivated
from app.modules.auth.domain.events.user_created import UserCreated
from app.modules.auth.domain.events.user_deactivated import UserDeactivated

from app.modules.knowledge_base.domain.enums.recalculation_trigger import RecalculationTrigger
from app.modules.knowledge_base.domain.enums.weekday import Weekday
from app.modules.knowledge_base.domain.events.similarity_graph_recalculated import (
	SimilarityGraphRecalculated,
)
from app.modules.knowledge_base.domain.events.similarity_graph_recalculation_failed import (
	SimilarityGraphRecalculationFailed,
)
from app.modules.knowledge_base.domain.events.similarity_recalculation_schedule_updated import (
	SimilarityRecalculationScheduleUpdated,
)
from app.modules.knowledge_base.domain.events.ticket_batch_import_failed import TicketBatchImportFailed

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

# Weekday.value is the three-letter cron code the scheduler consumes, never anything a person was
# meant to read. Same arrangement as the status labels below: a display-only mapping that lives
# here because notification text is the only place these are read by a human.
_WEEKDAY_LABELS_FR: dict[Weekday, str] = {
	Weekday.MONDAY: "lundi",
	Weekday.TUESDAY: "mardi",
	Weekday.WEDNESDAY: "mercredi",
	Weekday.THURSDAY: "jeudi",
	Weekday.FRIDAY: "vendredi",
	Weekday.SATURDAY: "samedi",
	Weekday.SUNDAY: "dimanche",
}

# Status.value stays an English constant (it's an API contract value, read by the frontend's
# own statusConfig to render badges) -- this is a display-only label for notification text,
# mirroring statusConfig's French labels so the two surfaces never say different things.
_STATUS_LABELS_FR: dict[Status, str] = {
	Status.OPEN: "ouvert",
	Status.IN_PROGRESS: "en cours",
	Status.TRANSFERRED: "transféré",
	Status.RESOLVED: "résolu",
	Status.CLOSED: "clôturé",
}


# Auth's FunctionalTeam is a separate enum from Ticket Management's above -- same two members,
# different module, and this one describes a person rather than a ticket. Both display as the
# same two French words the frontend already shows, which is the point of naming them here.
_FUNCTIONAL_TEAM_LABELS_FR: dict[AuthFunctionalTeam, str] = {
	AuthFunctionalTeam.SUPPORT: "Support",
	AuthFunctionalTeam.CONFIGURATION: "Paramétrage",
}


# Which door the pass came through, written as the whole subject of the sentence rather than as an
# adjective to drop into one. The three read differently enough that a shared frame with a word
# swapped into it produces French nobody would write: "le recalcul lancé manuellement de la base
# de connaissances" separates the participle from what it qualifies. Each is a phrase that stands
# on its own and takes a verb.
#
# The enum is carried on both outcome events precisely so a reader can tell "the Tuesday night pass
# failed" from "the pass somebody started a minute ago failed" -- two facts calling for different
# reactions, and the same record without this.
_RECALCULATION_SUBJECT_FR: dict[RecalculationTrigger, str] = {
	RecalculationTrigger.SCHEDULED: "Le recalcul planifié de la base de connaissances",
	RecalculationTrigger.MANUAL: "Le recalcul lancé manuellement",
	RecalculationTrigger.BATCH_IMPORT: "Le recalcul déclenché par un import de tickets",
}


# Who each broadcast is for, named as the permission that defines them rather than as a role.
# These are the audiences with no single obvious recipient -- there is no assignee, no author and
# no affected user to send to, only "whoever can act on this" -- and that is a permission by
# definition. Delegating one of these permissions moves its notifications with it, which is the
# whole of what delegating it was supposed to mean.
#
# The graph's state goes to whoever can *see* it rather than only to whoever can rebuild it: a
# stale graph changes what every reader of that page is looking at, and a notification saying so
# is worth having even when the reader's answer is to ask somebody else to act.
_SIMILARITY_GRAPH_AUDIENCE = "knowledge_base.read_recalculation"
# The import's own permission, not the graph's: what these announce is an upload that failed and
# may need re-running, which is the uploader's job rather than the maintainer's.
_BATCH_IMPORT_AUDIENCE = "knowledge_base.batch_import"
# A signup lands inactive and stays that way until somebody activates it, so the audience is the
# people who can perform exactly that act. They necessarily hold `user.read_all` too -- the
# catalog declares it a prerequisite of `user.activate` -- which is what makes this
# notification's deep link into the users page reachable for every recipient rather than for
# whichever roles happen to bundle both.
_NEW_USER_AUDIENCE = "user.activate"

_MAX_LISTED_CAPABILITIES = 3
"""How many revoked capabilities a single notification spells out before counting the rest.

Revoking a permission takes everything that depended on it too, so one administrative act can
remove fifteen at once. Naming all of them turns a notification into a report nobody reads;
the audit log keeps the full set for whoever needs it.
"""


def _assignment_for(assignments: Iterable[ApplicationAssignment], assignment_type: AssignmentType) -> str | None:
	return next((x.application.value for x in assignments if x.assignment_type == assignment_type), None)


def _applications_metadata(assignments: Iterable[ApplicationAssignment]) -> list[dict[str, str]]:
	"""Ordered, because the event carries a set and a set has no order to preserve."""
	return sorted(
		({"application": x.application.value, "assignment_type": x.assignment_type.value} for x in assignments),
		key=lambda entry: (entry["application"], entry["assignment_type"]),
	)


def _organizational_identity_sentence(
	functional_team: AuthFunctionalTeam, assignments: Iterable[ApplicationAssignment]
) -> str:
	"""Where the recipient now stands, in one sentence.

	Holding no application is spelled out rather than left as an empty clause: it is an
	ordinary state, and a notification that trailed off would read like the message was
	truncated.
	"""
	assignments = list(assignments)
	primary = _assignment_for(assignments, AssignmentType.PRIMARY)
	backup = _assignment_for(assignments, AssignmentType.BACKUP)
	team = _FUNCTIONAL_TEAM_LABELS_FR[functional_team]
	if primary is not None and backup is not None:
		scope = f"avec {primary} en application principale et {backup} en application de secours"
	elif primary is not None:
		scope = f"avec {primary} en application principale"
	elif backup is not None:
		scope = f"avec {backup} en application de secours"
	else:
		scope = "sans application affectée"
	return f"Vous êtes désormais rattaché à l'équipe {team}, {scope}."


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
			UserRoleChanged: self._user_role_changed,
			UserOrganizationalIdentityChanged: self._user_organizational_identity_changed,
			PermissionGrantedToUser: self._permission_granted,
			PermissionRevokedFromUser: self._permission_revoked,
			RolePermissionGranted: self._role_permission_granted,
			RolePermissionRevoked: self._role_permission_revoked,
			UserCreated: self._user_created,
			SimilarityRecalculationScheduleUpdated: self._similarity_schedule_updated,
			SimilarityGraphRecalculated: self._similarity_recalculation_completed,
			SimilarityGraphRecalculationFailed: self._similarity_recalculation_failed,
			TicketBatchImportFailed: self._batch_import_failed,
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

	@staticmethod
	def _lead_in(description: str) -> str:
		"""A Permission's seeded `description` reads as a standalone sentence (capitalized,
		e.g. "Changer la priorité d'un ticket.") -- lowercase its first letter so it flows
		naturally after a fixed lead-in ("Vous pouvez désormais : ...") instead of
		reconstructing a sentence from the permission's `resource.verb` name, which isn't
		regular enough to parse (half the catalog uses multi-word verbs like
		`change_priority` or `grant_to_role`)."""
		return description[:1].lower() + description[1:] if description else description

	@classmethod
	def _capability_list(cls, permissions: list[PermissionDTO]) -> str:
		"""What a revocation took away, as one readable clause after a fixed lead-in.

		A revocation carries every permission that depended on it, so this can be fifteen
		descriptions at once -- more than anyone reads in a notification. Three are named and
		the rest counted, which tells the recipient what changed without turning a notification
		into a report; the audit log has the full list for anyone who needs it.
		"""
		described = sorted(cls._lead_in(permission.description).rstrip(".") for permission in permissions)
		if len(described) <= _MAX_LISTED_CAPABILITIES:
			return f"{', '.join(described)}."
		remaining = len(described) - _MAX_LISTED_CAPABILITIES
		listed = ", ".join(described[:_MAX_LISTED_CAPABILITIES])
		return f"{listed}, et {remaining} autre{'s' if remaining > 1 else ''} action{'s' if remaining > 1 else ''}."

	# -- Ticket Management ---------------------------------------------------

	async def _ticket_reassigned(self, event: TicketReassigned) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [event.assignee_id],
			title="Ticket réaffecté", message=f'Vous avez été affecté au ticket « {ticket.title} ».',
			type=NotificationType.TICKET_ASSIGNED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title},
		)

	async def _priority_changed(self, event: PriorityChanged) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Priorité du ticket modifiée",
			message=f'La priorité de « {ticket.title} » est passée de {event.old_priority.value} à {event.new_priority.value}.',
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
		old_label = _STATUS_LABELS_FR[event.old_status]
		new_label = _STATUS_LABELS_FR[event.new_status]
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Statut du ticket modifié",
			message=f'Le statut de « {ticket.title} » est passé de {old_label} à {new_label}.',
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
			title="Nouveau commentaire", message=f'Un nouveau commentaire a été ajouté à « {ticket.title} ».',
			type=NotificationType.COMMENT_ADDED, action=OpenCommentAction(event.ticket_id, event.comment_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "comment_id": str(event.comment_id)},
		)

	async def _comment_edited(self, event: CommentEdited) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Commentaire modifié", message=f'Un commentaire sur « {ticket.title} » a été modifié.',
			type=NotificationType.COMMENT_EDITED, action=OpenCommentAction(event.ticket_id, event.comment_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "comment_id": str(event.comment_id)},
		)

	async def _comment_deleted(self, event: CommentDeleted) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Commentaire supprimé", message=f'Un commentaire sur « {ticket.title} » a été supprimé.',
			type=NotificationType.COMMENT_DELETED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "comment_id": str(event.comment_id)},
		)

	async def _attachment_added(self, event: AttachmentAdded) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Nouvelle pièce jointe", message=f'Une nouvelle pièce jointe a été ajoutée à « {ticket.title} ».',
			type=NotificationType.ATTACHMENT_ADDED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "attachment_id": str(event.attachment_id)},
		)

	async def _attachment_deleted(self, event: AttachmentDeleted) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Pièce jointe supprimée", message=f'Une pièce jointe de « {ticket.title} » a été supprimée.',
			type=NotificationType.ATTACHMENT_DELETED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "attachment_id": str(event.attachment_id)},
		)

	async def _ticket_archived(self, event: TicketArchived) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Ticket archivé", message=f'« {ticket.title} » a été archivé.',
			type=NotificationType.TICKET_ARCHIVED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title},
		)

	async def _ticket_restored(self, event: TicketRestored) -> list[Notification]:
		ticket = await self._recipients.get_ticket(event.ticket_id)
		if ticket is None:
			return []
		return self._for_recipients(
			event, [ticket.assignee_id],
			title="Ticket restauré", message=f'« {ticket.title} » a été restauré.',
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
			title="Ticket transféré vers votre équipe", message=f'« {ticket.title} » a été transféré vers {event.transferred_to.value}.',
			type=NotificationType.TICKET_TRANSFERRED, action=OpenTicketAction(event.ticket_id),
			metadata={"ticket_id": str(event.ticket_id), "ticket_title": ticket.title, "transferred_to": event.transferred_to.value},
		)

	# -- Auth ------------------------------------------------------------------

	async def _user_activated(self, event: UserActivated) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Compte activé", message="Votre compte a été activé.",
			type=NotificationType.ACCOUNT_ACTIVATED, action=None,
			metadata={"user_id": str(event.user_id)},
		)

	async def _user_deactivated(self, event: UserDeactivated) -> list[Notification]:
		return self._for_recipients(
			event, [event.user_id],
			title="Compte désactivé", message="Votre compte a été désactivé.",
			type=NotificationType.ACCOUNT_DEACTIVATED, action=None,
			metadata={"user_id": str(event.user_id)},
		)

	async def _user_role_changed(self, event: UserRoleChanged) -> list[Notification]:
		role_name = await self._recipients.get_role_name(event.new_role_id)
		if role_name is None:
			return []
		# One notification naming only the role the recipient now holds. What they no longer
		# hold is not something they can act on, and the "attribué"/"retiré" pair this replaced
		# announced a single administrative change twice.
		return self._for_recipients(
			event, [event.user_id],
			title="Rôle modifié", message=f'Votre rôle est désormais « {role_name} ».',
			type=NotificationType.ROLE_CHANGED, action=None,
			metadata={
				"user_id": str(event.user_id),
				"previous_role_id": str(event.previous_role_id),
				"role_id": str(event.new_role_id),
			},
		)

	async def _user_organizational_identity_changed(self, event: UserOrganizationalIdentityChanged) -> list[Notification]:
		"""What the recipient staffs now -- not what they used to.

		Same choice `_user_role_changed` makes: a person can act on where they have been put,
		not on where they no longer are, and the before/after pair is in the audit log for
		anyone reconstructing the decision. No action either -- the only page that shows this
		is the administration user list, which the recipient of this notification generally
		cannot open.
		"""
		return self._for_recipients(
			event, [event.user_id],
			title="Affectation modifiée",
			message=_organizational_identity_sentence(event.new_functional_team, event.new_application_assignments),
			type=NotificationType.ORGANIZATIONAL_IDENTITY_CHANGED, action=None,
			metadata={
				"user_id": str(event.user_id),
				"previous_functional_team": event.previous_functional_team.value,
				"functional_team": event.new_functional_team.value,
				"previous_applications": _applications_metadata(event.previous_application_assignments),
				"applications": _applications_metadata(event.new_application_assignments),
			},
		)

	async def _permission_granted(self, event: PermissionGrantedToUser) -> list[Notification]:
		permission = await self._recipients.get_permission(event.permission_id)
		if permission is None:
			return []
		return self._for_recipients(
			event, [event.user_id],
			title="Permission accordée", message=f"Vous pouvez désormais : {self._lead_in(permission.description)}",
			type=NotificationType.PERMISSION_GRANTED, action=None,
			metadata={"user_id": str(event.user_id), "permission_id": str(event.permission_id)},
		)

	async def _permission_revoked(self, event: PermissionRevokedFromUser) -> list[Notification]:
		permissions = await self._recipients.get_permissions(event.permission_ids)
		if not permissions:
			return []
		return self._for_recipients(
			event, [event.user_id],
			title="Permission retirée" if len(permissions) == 1 else "Permissions retirées",
			message=f"Vous ne pouvez plus : {self._capability_list(permissions)}",
			type=NotificationType.PERMISSION_REVOKED, action=None,
			metadata={"user_id": str(event.user_id), "permission_ids": sorted(str(x) for x in event.permission_ids)},
		)

	async def _role_permission_granted(self, event: RolePermissionGranted) -> list[Notification]:
		recipient_ids = await self._recipients.active_user_ids_with_role(event.role_id)
		role_name = await self._recipients.get_role_name(event.role_id)
		permission = await self._recipients.get_permission(event.permission_id)
		if role_name is None or permission is None:
			return []
		return self._for_recipients(
			event, recipient_ids,
			title="Permissions du rôle modifiées",
			message=f'Les membres du rôle « {role_name} » peuvent désormais : {self._lead_in(permission.description)}',
			type=NotificationType.ROLE_PERMISSION_GRANTED, action=None,
			metadata={"role_id": str(event.role_id), "permission_id": str(event.permission_id)},
		)

	async def _role_permission_revoked(self, event: RolePermissionRevoked) -> list[Notification]:
		recipient_ids = await self._recipients.active_user_ids_with_role(event.role_id)
		role_name = await self._recipients.get_role_name(event.role_id)
		permissions = await self._recipients.get_permissions(event.permission_ids)
		if role_name is None or not permissions:
			return []
		return self._for_recipients(
			event, recipient_ids,
			title="Permissions du rôle modifiées",
			message=f'Les membres du rôle « {role_name} » ne peuvent plus : {self._capability_list(permissions)}',
			type=NotificationType.ROLE_PERMISSION_REVOKED, action=None,
			metadata={"role_id": str(event.role_id), "permission_ids": sorted(str(x) for x in event.permission_ids)},
		)

	async def _user_created(self, event: UserCreated) -> list[Notification]:
		welcome = self._for_recipients(
			event, [event.user_id],
			title="Bienvenue", message=f"Bienvenue, {event.display_name} ! Votre compte a été créé.",
			type=NotificationType.ACCOUNT_CREATED, action=None,
			metadata={"user_id": str(event.user_id)},
		)
		admin_ids = await self._recipients.active_user_ids_with_permission(_NEW_USER_AUDIENCE)
		admin_ids = admin_ids - {event.user_id}
		announcements = self._for_recipients(
			event, admin_ids,
			title="Nouvel utilisateur inscrit", message=f"{event.display_name} ({event.email}) vient de rejoindre la plateforme.",
			type=NotificationType.NEW_USER_REGISTERED, action=OpenUserAction(event.user_id),
			metadata={"user_id": str(event.user_id), "email": event.email, "display_name": event.display_name},
		)
		return welcome + announcements

	# -- Knowledge Base --------------------------------------------------------
	#
	# None of these carries an action: the pages they concern are administrative screens with no
	# per-resource route to deep-link into, and inventing an action type the frontend does not yet
	# interpret would put a dead click target in the bell. Every Auth notification above is
	# action-less for the same reason.
	#
	# A completed recalculation used to be withheld here as routine success, on the argument that
	# a notification list filled with things going right is one where failures stop being noticed.
	# What that missed is that almost everything this module does is invisible by construction:
	# the passes run outside working hours, write to a store nobody reads directly, and leave the
	# graph looking identical whether they ran or not. Announcing only the failures made silence
	# ambiguous -- it meant a healthy graph, a scheduler that never fired, and a process that was
	# restarted before its window, all at once. Announcing both makes an absent success readable,
	# which is the fact an administrator was actually missing. The volume argument survives on its
	# own terms: this is twice a week plus whatever is asked for by hand.
	#
	# SimilarityRecalculationRequested stays absent. It is the administrator's own button press,
	# answered by the button itself and by the status card next to it, and the pass it starts
	# reports its own outcome here a few minutes later.

	async def _similarity_schedule_updated(self, event: SimilarityRecalculationScheduleUpdated) -> list[Notification]:
		"""Tell everyone else who can see this schedule that the rebuild window moved, or stopped.

		The one who set it is excluded by the shared guard, which is right here: they just did it.
		Nobody else has another way to find out -- the change takes effect on a background pass that
		runs outside working hours, so its only visible symptom is similar-incident results quietly
		ceasing to improve, weeks later.
		"""
		recipient_ids = await self._recipients.active_user_ids_with_permission(_SIMILARITY_GRAPH_AUDIENCE)
		if event.enabled:
			days = self._day_list(event.days_of_week)
			message = (
				f"Le recalcul complet de la base de connaissances est désormais planifié "
				f"{days} à {event.hour:02d}:{event.minute:02d} ({event.timezone})."
			)
		else:
			message = (
				"Le recalcul complet de la base de connaissances a été désactivé. Les incidents "
				"similaires resteront ceux du dernier calcul effectué."
			)
		return self._for_recipients(
			event, recipient_ids,
			title="Planification du recalcul modifiée", message=message,
			type=NotificationType.SIMILARITY_SCHEDULE_UPDATED, action=None,
			metadata={
				"enabled": event.enabled,
				"days_of_week": [day.value for day in event.days_of_week],
				"hour": event.hour, "minute": event.minute, "timezone": event.timezone,
			},
		)

	async def _similarity_recalculation_completed(self, event: SimilarityGraphRecalculated) -> list[Notification]:
		"""Say that a pass ran, what it went through, and how long it took.

		The counterpart of the failure below, and told to the same audience for the same reason:
		what changed is the answer every similar-incident card in the product gives, and nothing
		about the product looks different afterwards. Naming the trigger is what makes the message
		worth reading rather than noise -- a Tuesday-night pass finishing is a heartbeat, a pass
		finishing four minutes after somebody pressed the button is a reply to them.

		`actor_id` is None on this event, so the shared guard excludes nobody: the administrator
		who asked for a manual pass is told it finished, which is the one message here with a
		person waiting for it. That is deliberate and not an oversight of the guard -- the guard
		exists so nobody is told what they just did, and this reports what happened afterwards.

		`sources_without_results` is reported only when there is something to report. It is a
		correct outcome of a threshold rather than a fault, but a pass where it dominates is the
		signature of a mis-calibrated one, and that is invisible anywhere else.
		"""
		recipient_ids = await self._recipients.active_user_ids_with_permission(_SIMILARITY_GRAPH_AUDIENCE)
		message = (
			f"{_RECALCULATION_SUBJECT_FR[event.trigger]} est terminé : "
			f"{_count_fr(event.items_processed)} ticket(s) analysé(s) et "
			f"{_count_fr(event.results_written)} suggestion(s) reconstruite(s) en "
			f"{_duration_fr(event.duration_seconds)}."
		)
		if event.sources_without_results > 0:
			message += (
				f" {_count_fr(event.sources_without_results)} ticket(s) n'ont aucun incident "
				f"similaire au-dessus du seuil de pertinence."
			)
		return self._for_recipients(
			event, recipient_ids,
			title="Recalcul de similarité terminé", message=message,
			type=NotificationType.SIMILARITY_RECALCULATION_COMPLETED, action=None,
			metadata={
				"trigger": event.trigger.value,
				"items_processed": event.items_processed,
				"results_written": event.results_written,
				"sources_without_results": event.sources_without_results,
				"duration_seconds": round(event.duration_seconds, 1),
			},
		)

	async def _similarity_recalculation_failed(self, event: SimilarityGraphRecalculationFailed) -> list[Notification]:
		"""Tell everyone who can see the graph that it is stale, because nothing else will.

		The most useful notification in this module's set, and the one whose absence was the real
		gap: a failed pass leaves the previous graph in place, keeps its next scheduled firing, and
		changes nothing an engineer can see. Without this, three failed runs in a row look exactly
		like three quiet weeks, and every similar-incident card keeps answering from a corpus that
		has moved on.

		actor_id is None on this event, so the shared guard excludes nobody and the whole audience is
		told -- which is correct: a scheduled pass failing at 20:00 is nobody's action, and whoever
		triggered a manual one is as entitled to know as the rest.
		"""
		recipient_ids = await self._recipients.active_user_ids_with_permission(_SIMILARITY_GRAPH_AUDIENCE)
		return self._for_recipients(
			event, recipient_ids,
			title="Échec du recalcul de similarité",
			message=(
				f"{_RECALCULATION_SUBJECT_FR[event.trigger]} a échoué au bout de "
				f"{_duration_fr(event.duration_seconds)} ({event.reason}). Les incidents "
				f"similaires affichés restent ceux du dernier calcul réussi."
			),
			type=NotificationType.SIMILARITY_RECALCULATION_FAILED, action=None,
			metadata={"trigger": event.trigger.value, "reason": event.reason},
		)

	async def _batch_import_failed(self, event: TicketBatchImportFailed) -> list[Notification]:
		"""Tell whoever can run an import that one failed, and whether it left anything behind.

		The one place in this mapper where the acting user is notified of their own action, and
		the exception is deliberate. The shared guard exists so nobody is told what they just did;
		this tells them what went wrong *afterwards*, and when the compensation itself failed it
		carries the only durable instruction for repairing it. The uploader does see that in the
		error response, but a response is read once, by one person, who may well close the tab --
		and the repair is a backfill rather than another upload, so getting it wrong is expensive.
		Everyone else holding the permission is told for the ordinary reason: tickets with no corpus entry are
		invisible to every similarity search until somebody acts.
		"""
		if event.tickets_discarded:
			message = (
				f"L'import de {event.ticket_count} ticket(s) {event.application.value} a échoué et "
				f"a été annulé ({event.reason}). Aucun ticket n'a été conservé."
			)
		else:
			message = (
				f"L'import de {event.ticket_count} ticket(s) {event.application.value} a échoué "
				f"({event.reason}) et n'a pas pu être annulé. Ces tickets subsistent en base sans "
				f"entrée dans la base de connaissances : lancez le backfill pour les rattraper."
			)

		metadata = {
			"application": event.application.value, "ticket_count": event.ticket_count,
			"reason": event.reason, "tickets_discarded": event.tickets_discarded,
		}
		recipient_ids = await self._recipients.active_user_ids_with_permission(_BATCH_IMPORT_AUDIENCE)
		notifications = self._for_recipients(
			event, recipient_ids,
			title="Échec d'un import de tickets", message=message,
			type=NotificationType.BATCH_IMPORT_FAILED, action=None, metadata=metadata,
		)
		if event.actor_id is not None and event.actor_id not in {n.recipient_id for n in notifications}:
			notifications.append(
				self._notification(
					event, recipient_id=event.actor_id,
					title="Échec d'un import de tickets", message=message,
					type=NotificationType.BATCH_IMPORT_FAILED, action=None, metadata=metadata,
				)
			)
		return notifications

	@staticmethod
	def _day_list(days: tuple[Weekday, ...]) -> str:
		"""The configured days as French prose: "le mardi et le vendredi", not "tue,fri".

		Each day keeps its own article, which is what makes the recurring reading ("every Tuesday
		and every Friday") the natural one -- "le mardi et vendredi" reads as a single date.
		"""
		labels = [f"le {_WEEKDAY_LABELS_FR[day]}" for day in days]
		if len(labels) <= 1:
			return "".join(labels)
		return f"{', '.join(labels[:-1])} et {labels[-1]}"


# Named rather than written inline: it is U+202F, which looks exactly like a space in an
# editor and would be silently replaced by one on any careless edit.
_THOUSANDS_SEPARATOR_FR = chr(0x202F)


def _count_fr(value: int) -> str:
	"""A count as French writes it: 6830 -> "6 830", grouped with a narrow no-break space.

	Module-level rather than a method, and matching what `toLocaleString("fr-FR")` produces on
	the frontend -- the same number must not be grouped one way in the bell and another way on
	the page it is about.
	"""
	return f"{value:,}".replace(",", _THOUSANDS_SEPARATOR_FR)


def _duration_fr(seconds: float) -> str:
	"""How long a pass took, at the precision a reader of it cares about.

	Rounded to whole seconds and floored at one: a pass reported as having taken "0 s" reads as
	one that did not run, and the difference between 400ms and 600ms is not what anybody is
	asking. Minutes and hours drop the units below them once they would only add noise.
	"""
	total = max(round(seconds), 1)
	hours, rest = divmod(total, 3600)
	minutes, remainder = divmod(rest, 60)
	if hours:
		return f"{hours} h {minutes:02d} min"
	if minutes:
		return f"{minutes} min {remainder:02d} s" if remainder else f"{minutes} min"
	return f"{remainder} s"
