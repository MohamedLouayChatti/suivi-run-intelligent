import type { components } from "@/types/api"

import {
  ANALYTICS,
  BATCH_IMPORT_WRITE,
  IDENTITY_WRITE,
  KB_SCHEDULE,
  ROLE_WRITE,
  STAFFING_WRITE,
  TICKET_WRITE,
  USERS,
  type QueryKeyPrefix,
} from "@/lib/cache-invalidation"

type NotificationType = components["schemas"]["NotificationType"]

/**
 * What each notification implies has gone stale for the person receiving it.
 *
 * This is the other half of the mutation-side groups: the same families of server
 * state, reached because somebody *else* changed them. The stream already delivered
 * these — every type below is in the backend's notified set, arrives over the open SSE
 * connection and raises a toast — but the cache was never told, so a permission could
 * be revoked, be announced on screen, and leave every gated control in the app still
 * rendering from the identity fetched at sign-in.
 *
 * Deliberately exhaustive rather than Partial: adding a member to NotificationType on
 * the backend and regenerating the API types should fail this file to compile, so the
 * question "what does this one make stale?" is answered when the notification is
 * introduced rather than silently defaulting to nothing.
 */
const INVALIDATED_BY: Record<NotificationType, QueryKeyPrefix[]> = {
  // Someone acted on a ticket the recipient is involved in. Same reach as performing
  // the action yourself, which is exactly the point.
  TICKET_ASSIGNED: TICKET_WRITE,
  TICKET_PRIORITY_CHANGED: TICKET_WRITE,
  TICKET_STATUS_CHANGED: TICKET_WRITE,
  COMMENT_ADDED: TICKET_WRITE,
  COMMENT_EDITED: TICKET_WRITE,
  COMMENT_DELETED: TICKET_WRITE,
  ATTACHMENT_ADDED: TICKET_WRITE,
  ATTACHMENT_DELETED: TICKET_WRITE,
  TICKET_ARCHIVED: TICKET_WRITE,
  TICKET_RESTORED: TICKET_WRITE,
  TICKET_TRANSFERRED: TICKET_WRITE,

  // Deactivation is the one entry whose refetch is expected to fail: /auth/me answers
  // 403 for an inactive account, which is precisely what the auth gate reads to replace
  // the application with "Accès refusé". Losing access mid-session should be immediate,
  // not something the user discovers on their next navigation.
  ACCOUNT_ACTIVATED: IDENTITY_WRITE,
  ACCOUNT_DEACTIVATED: IDENTITY_WRITE,

  PERMISSION_GRANTED: IDENTITY_WRITE,
  PERMISSION_REVOKED: IDENTITY_WRITE,

  // A role change, and any edit to a role's own permission set, rewrites the effective
  // permissions of everyone holding it.
  ROLE_CHANGED: ROLE_WRITE,
  ROLE_PERMISSION_GRANTED: ROLE_WRITE,
  ROLE_PERMISSION_REVOKED: ROLE_WRITE,
  // Historical: nothing produces these any more, a user holding exactly one role. Kept
  // mapped because notifications written under the old model still carry them.
  ROLE_ASSIGNED: ROLE_WRITE,
  ROLE_REVOKED: ROLE_WRITE,

  // Staffing decides which applications scope the recipient's ticket and analytics
  // collections, so the collections themselves are stale, not just the profile.
  ORGANIZATIONAL_IDENTITY_CHANGED: STAFFING_WRITE,

  // Told to whoever administers users; the only thing that moved is the roster.
  ACCOUNT_CREATED: [USERS],
  NEW_USER_REGISTERED: [USERS],

  // The recalculation card shows the schedule and a live `running` flag, and all three
  // of these are that flag changing.
  SIMILARITY_SCHEDULE_UPDATED: [KB_SCHEDULE],
  SIMILARITY_RECALCULATION_COMPLETED: [KB_SCHEDULE],
  SIMILARITY_RECALCULATION_FAILED: [KB_SCHEDULE],

  // A failed import is compensating: the tickets it created were deleted again. Anything
  // that read them in between is holding rows that no longer exist.
  BATCH_IMPORT_FAILED: BATCH_IMPORT_WRITE,

  APPLICATION_HEALTH_CRITICAL: [ANALYTICS],
}

function groupsForNotification(type: NotificationType): QueryKeyPrefix[] {
  return INVALIDATED_BY[type] ?? []
}

export { groupsForNotification }
