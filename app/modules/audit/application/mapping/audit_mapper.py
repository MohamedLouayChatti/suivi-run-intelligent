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
from app.modules.ticket_management.domain.events.tickets_import_discarded import TicketsImportDiscarded
from app.modules.ticket_management.domain.events.tickets_imported import TicketsImported

from app.modules.auth.domain.events.permission_granted_to_user import PermissionGrantedToUser
from app.modules.auth.domain.events.permission_revoked_from_user import PermissionRevokedFromUser
from app.modules.auth.domain.events.user_role_changed import UserRoleChanged
from app.modules.auth.domain.events.role_permission_granted import RolePermissionGranted
from app.modules.auth.domain.events.role_permission_revoked import RolePermissionRevoked
from app.modules.auth.domain.events.user_activated import UserActivated
from app.modules.auth.domain.events.user_created import UserCreated
from app.modules.auth.domain.events.user_deactivated import UserDeactivated
from app.modules.auth.domain.events.user_updated import UserUpdated

from app.modules.knowledge_base.domain.events.similarity_graph_recalculated import SimilarityGraphRecalculated
from app.modules.knowledge_base.domain.events.similarity_graph_recalculation_failed import (
	SimilarityGraphRecalculationFailed,
)
from app.modules.knowledge_base.domain.events.similarity_recalculation_requested import (
	SimilarityRecalculationRequested,
)
from app.modules.knowledge_base.domain.events.similarity_recalculation_schedule_updated import (
	SimilarityRecalculationScheduleUpdated,
)
from app.modules.knowledge_base.domain.events.ticket_batch_import_failed import TicketBatchImportFailed


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
			TicketsImported: self._tickets_imported,
			TicketsImportDiscarded: self._tickets_import_discarded,
			UserCreated: self._user_created,
			UserUpdated: self._user_updated,
			UserActivated: self._user_activated,
			UserDeactivated: self._user_deactivated,
			UserRoleChanged: self._user_role_changed,
			PermissionGrantedToUser: self._permission_granted_to_user,
			PermissionRevokedFromUser: self._permission_revoked_from_user,
			RolePermissionGranted: self._role_permission_granted,
			RolePermissionRevoked: self._role_permission_revoked,
			SimilarityRecalculationScheduleUpdated: self._similarity_recalculation_schedule_updated,
			SimilarityRecalculationRequested: self._similarity_recalculation_requested,
			SimilarityGraphRecalculated: self._similarity_graph_recalculated,
			SimilarityGraphRecalculationFailed: self._similarity_graph_recalculation_failed,
			TicketBatchImportFailed: self._ticket_batch_import_failed,
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

	def _tickets_imported(self, event: TicketsImported) -> AuditEntry:
		"""One entry for a whole batch, mirroring the one event it publishes.

		The ticket ids are counted rather than listed. A payload holding a thousand UUIDs would be
		the largest row in this table by an order of magnitude, and what an audit reader is asking
		is who loaded how much into which application -- the tickets themselves are in the tickets
		table, where a reader can filter them by the application and the moment recorded here.
		"""
		return self._entry(
			event, module="ticket_management", event_type="TicketsImported",
			action="ticket.imported", resource_type="ticket",
			payload={"application": event.application.value, "ticket_count": len(event.ticket_ids)},
		)

	def _tickets_import_discarded(self, event: TicketsImportDiscarded) -> AuditEntry:
		"""The compensating entry, recorded rather than allowed to cancel out the import above it.

		Both happened, and an audit log that showed neither would quietly lose the fact that a
		batch of tickets appeared and was taken away again. `reason` is the failure that forced it,
		which is the part a reader coming back to this later actually needs.
		"""
		return self._entry(
			event, module="ticket_management", event_type="TicketsImportDiscarded",
			action="ticket.import_discarded", resource_type="ticket",
			payload={
				"application": event.application.value,
				"ticket_count": len(event.ticket_ids),
				"reason": event.reason,
			},
		)

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

	def _user_role_changed(self, event: UserRoleChanged) -> AuditEntry:
		return self._entry(
			event, module="auth", event_type="UserRoleChanged",
			action="user.role_changed", resource_type="user",
			payload={
				"user_id": str(event.user_id),
				"previous_role_id": str(event.previous_role_id),
				"new_role_id": str(event.new_role_id),
			},
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

	# -- Knowledge Base ----------------------------------------------------
	#
	# Two resource_type values appear here that no InstanceAuthorizationPolicy is registered
	# under, which is a deliberate widening of the vocabulary rather than a slip. Every other
	# resource_type in this file names something a caller can be authorized against one instance
	# of; a recalculation schedule is a single row with no owner and a similarity graph is the
	# whole corpus, so neither has an instance to authorize and the module that owns them
	# registers no policy at all. Naming them anyway is what lets an audit reader filter these
	# entries the same way they filter every other kind.

	def _similarity_recalculation_schedule_updated(self, event: SimilarityRecalculationScheduleUpdated) -> AuditEntry:
		"""Who changed when the whole similarity graph gets rebuilt.

		The only database-backed configuration in this system, so this is the only audit entry
		that records a setting rather than an action on a resource. The whole schedule goes into
		the payload rather than a diff: reconstructing what changed is reading this entry against
		the one before it, which is a thing an append-only log is good at, whereas a diff computed
		at write time would be a second answer free to disagree with the row it describes.
		"""
		return self._entry(
			event, module="knowledge_base", event_type="SimilarityRecalculationScheduleUpdated",
			action="knowledge_base.recalculation_schedule_updated", resource_type="recalculation_schedule",
			payload={
				"enabled": event.enabled,
				"days_of_week": [day.value for day in event.days_of_week],
				"hour": event.hour,
				"minute": event.minute,
				"timezone": event.timezone,
			},
		)

	def _similarity_recalculation_requested(self, event: SimilarityRecalculationRequested) -> AuditEntry:
		"""An administrator started a full recalculation by hand.

		The payload is empty, and legitimately so: there is nothing to configure about a run, so
		everything this entry has to say is already in the envelope -- who, and when. It is the
		only record anywhere of who started a given pass, since the run itself outlives the
		request that asked for it and carries no actor by the time it reports back.
		"""
		return self._entry(
			event, module="knowledge_base", event_type="SimilarityRecalculationRequested",
			action="knowledge_base.recalculation_requested", resource_type="similarity_graph",
			payload={},
		)

	def _similarity_graph_recalculated(self, event: SimilarityGraphRecalculated) -> AuditEntry:
		"""A full pass finished, and what it produced.

		These entries are the run history this module was told it would need a second table for.
		Filtering the log by this event type answers "when did the last rebuild run and what did
		it find" from rows that were being written anyway, which is why `last_run_at` no longer
		needs a home of its own.

		`sources_without_results` is worth keeping across runs rather than only logging: one pass
		where most sources come back empty is expected, but a *trend* of them is the signature of
		a mis-calibrated threshold, and a trend is exactly what a log line cannot show.
		"""
		return self._entry(
			event, module="knowledge_base", event_type="SimilarityGraphRecalculated",
			action="knowledge_base.similarity_graph_recalculated", resource_type="similarity_graph",
			payload={
				"trigger": event.trigger.value,
				"items_processed": event.items_processed,
				"results_written": event.results_written,
				"sources_without_results": event.sources_without_results,
				"duration_seconds": round(event.duration_seconds, 3),
			},
		)

	def _similarity_graph_recalculation_failed(self, event: SimilarityGraphRecalculationFailed) -> AuditEntry:
		"""A pass started and did not finish, so the graph everyone reads is still the old one.

		Recorded rather than left to the log because staleness compounds silently: the schedule
		keeps its next firing, nothing in the API says the graph is out of date, and three failed
		runs in a row look exactly like three quiet weeks. Read against the successful entries
		above, this is what makes "how long has the graph actually been stale" answerable.
		"""
		return self._entry(
			event, module="knowledge_base", event_type="SimilarityGraphRecalculationFailed",
			action="knowledge_base.similarity_graph_recalculation_failed", resource_type="similarity_graph",
			payload={
				"trigger": event.trigger.value,
				"reason": event.reason,
				"duration_seconds": round(event.duration_seconds, 3),
			},
		)

	def _ticket_batch_import_failed(self, event: TicketBatchImportFailed) -> AuditEntry:
		"""A batch was created and then could not be brought into the knowledge base.

		The entry that closes a real hole in this log. A batch import that succeeds leaves one
		TicketsImported entry, and one that fails and unwinds cleanly leaves that plus a
		TicketsImportDiscarded -- but when the unwind itself fails, the discard event is never
		published, and the log was left showing an import indistinguishable from a successful one
		while the tickets sat in the database with nothing in the corpus behind them.

		`tickets_discarded` is the field that distinguishes those two, and `ticket_count` says how
		much was left behind when it is False. Counted rather than listed, for the same reason
		TicketsImported counts them: the tickets are in the tickets table, filterable by the
		application and moment recorded here.
		"""
		return self._entry(
			event, module="knowledge_base", event_type="TicketBatchImportFailed",
			action="knowledge_base.batch_import_failed", resource_type="ticket",
			payload={
				"application": event.application.value,
				"ticket_count": event.ticket_count,
				"reason": event.reason,
				"tickets_discarded": event.tickets_discarded,
			},
		)
