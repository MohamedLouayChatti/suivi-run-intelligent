from __future__ import annotations

from app.modules.audit.application.mapping.audit_mapper import AuditMapper
from app.modules.audit.infrastructure.events.handlers.audit_event_handler import AuditEventHandler
from app.modules.audit.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.shared.events.subscriptions import SubscriptionRegistry
from app.shared.security.instance_authorization_registry import InstanceAuthorizationRegistry

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
from app.modules.auth.domain.events.user_organizational_identity_changed import UserOrganizationalIdentityChanged
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

# Knowledge Base joins the two modules already audited here, and brings the first entries that are
# not a person acting on a resource: two of its five are outcomes of a background pass with no
# actor at all. They belong in this log for the same reason the rest do -- something happened that
# a reader coming back later needs to be able to establish -- and the three that *do* have an actor
# are every permissioned action that module exposes, none of which left a trace before.
#
# SimilarityResultsGenerated is deliberately not among them. It fires once per ticket creation with
# no actor and no decision behind it, recording that a computation ran; TicketCreated is already
# written at the same instant, so auditing it too would double this table's growth rate to say
# something the log already says better.
AUDITED_EVENT_TYPES = (
	TicketCreated, TicketStatusChanged, TicketReassigned, PriorityChanged, TicketTransferred,
	CommentAdded, CommentEdited, CommentDeleted, AttachmentAdded, AttachmentDeleted,
	TicketArchived, TicketRestored, JiraDetailsUpdated, OperationalHighlightChanged,
	TicketsImported, TicketsImportDiscarded,
	UserCreated, UserUpdated, UserActivated, UserDeactivated, UserRoleChanged,
	UserOrganizationalIdentityChanged,
	PermissionGrantedToUser, PermissionRevokedFromUser, RolePermissionGranted, RolePermissionRevoked,
	SimilarityRecalculationScheduleUpdated, SimilarityRecalculationRequested,
	SimilarityGraphRecalculated, SimilarityGraphRecalculationFailed, TicketBatchImportFailed,
)


def register_subscriptions(registry: SubscriptionRegistry) -> None:
	"""Subscribe Audit's single generic handler to every audited domain event type.

	One handler instance is shared across all event types -- it stays thin because
	AuditMapper (not the handler) knows how to translate each event type.
	"""
	handler = AuditEventHandler(SqlAlchemyUnitOfWork, AuditMapper())
	for event_type in AUDITED_EVENT_TYPES:
		registry.subscribe(event_type, handler)


def register_instance_authorization_policies(registry: InstanceAuthorizationRegistry) -> None:
	"""Audit has no per-resource instance authorization: both collection and
	single-entry reads are gated by the audit.read permission at the route level.

	audit.read is seeded onto Admin alone, but nothing here requires that -- granting it to
	a dedicated auditor role is all it takes to open the log to a non-administrator."""
	return None
