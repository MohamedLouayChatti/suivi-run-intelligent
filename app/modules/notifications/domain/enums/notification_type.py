from __future__ import annotations

from enum import StrEnum


class NotificationType(StrEnum):
	TICKET_ASSIGNED = "TICKET_ASSIGNED"
	TICKET_PRIORITY_CHANGED = "TICKET_PRIORITY_CHANGED"
	TICKET_STATUS_CHANGED = "TICKET_STATUS_CHANGED"
	COMMENT_ADDED = "COMMENT_ADDED"
	COMMENT_EDITED = "COMMENT_EDITED"
	COMMENT_DELETED = "COMMENT_DELETED"
	ATTACHMENT_ADDED = "ATTACHMENT_ADDED"
	ATTACHMENT_DELETED = "ATTACHMENT_DELETED"
	TICKET_ARCHIVED = "TICKET_ARCHIVED"
	TICKET_RESTORED = "TICKET_RESTORED"
	TICKET_TRANSFERRED = "TICKET_TRANSFERRED"
	ACCOUNT_ACTIVATED = "ACCOUNT_ACTIVATED"
	ACCOUNT_DEACTIVATED = "ACCOUNT_DEACTIVATED"
	ROLE_CHANGED = "ROLE_CHANGED"
	# Which applications the recipient staffs, and on which team. One member for both, because
	# the two are set together and refused together -- there is no change to one alone.
	ORGANIZATIONAL_IDENTITY_CHANGED = "ORGANIZATIONAL_IDENTITY_CHANGED"
	# Historical only: a user held a set of roles before, so gaining and losing one were two
	# separate things to be told about. They now hold exactly one, and any change to it is a
	# single ROLE_CHANGED. Kept because notifications written under the old model still carry
	# them -- nothing produces either any more.
	ROLE_ASSIGNED = "ROLE_ASSIGNED"
	ROLE_REVOKED = "ROLE_REVOKED"
	PERMISSION_GRANTED = "PERMISSION_GRANTED"
	PERMISSION_REVOKED = "PERMISSION_REVOKED"
	ROLE_PERMISSION_GRANTED = "ROLE_PERMISSION_GRANTED"
	ROLE_PERMISSION_REVOKED = "ROLE_PERMISSION_REVOKED"
	ACCOUNT_CREATED = "ACCOUNT_CREATED"
	NEW_USER_REGISTERED = "NEW_USER_REGISTERED"
	SIMILARITY_SCHEDULE_UPDATED = "SIMILARITY_SCHEDULE_UPDATED"
	# Both outcomes of one pass, and both are told. A completed rebuild was once left out as
	# routine success not worth a bell -- which held only while the failure was the sole thing
	# anyone could learn about a pass. It leaves an announced failure as the only sign the
	# rebuild exists, so silence reads as health whether the pass ran or the scheduler never
	# fired at all. Told together, an absent success is itself informative.
	SIMILARITY_RECALCULATION_COMPLETED = "SIMILARITY_RECALCULATION_COMPLETED"
	SIMILARITY_RECALCULATION_FAILED = "SIMILARITY_RECALCULATION_FAILED"
	BATCH_IMPORT_FAILED = "BATCH_IMPORT_FAILED"
