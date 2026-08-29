import type { QueryClient } from "@tanstack/react-query"

/**
 * What goes stale when — declared once, for both directions it is needed in: a
 * mutation the current user just performed, and a notification telling them someone
 * else performed one. Those two used to be answered separately, which is how the
 * second came to be answered not at all.
 */
type QueryKeyPrefix = readonly string[]

/**
 * One prefix per family of server state.
 *
 * Deliberately spelled literally rather than imported from each hook's own exported
 * key: a hook's `afterMutation` imports `invalidateGroups` from here, so reaching back
 * for `ticketDetailQueryKey` would close an import cycle. Invalidation matches by
 * prefix regardless, so naming the prefix one level above the per-hook keys is both
 * cycle-free and honest about what is actually being matched.
 *
 * Each prefix covers every key beneath it — TICKETS reaches the ticket list, the
 * paginated "active" tables, every open ticket detail and the history view, all four
 * being spelled under ["tickets", ...].
 */
const TICKETS = ["tickets"] as const
const ANALYTICS = ["analytics"] as const
const IDENTITY = ["auth", "me"] as const
const USERS = ["users"] as const
const ROLES = ["roles"] as const
const KB_SCHEDULE = ["knowledge-base", "recalculation-schedule"] as const

/**
 * Creating a ticket, or changing its state, assignee, priority, Jira details,
 * highlight, comments or attachments.
 *
 * ANALYTICS rides along because every figure on the Analyses page and both of the
 * Dashboard's personal widgets is computed from exactly the columns these writes
 * touch: a resolved ticket moves "Résolus cette semaine" as surely as it moves the
 * ticket list, and nothing in the app invalidated that until now.
 */
const TICKET_WRITE: QueryKeyPrefix[] = [TICKETS, ANALYTICS]

/**
 * A change to who someone is, or to what they may do — activation, a direct
 * permission grant or revocation.
 *
 * IDENTITY is the half missing everywhere before: /auth/me is fetched once per
 * session and backs every permission-gated control in the app, so a permission that
 * changes without it being refetched is a capability the interface never learns
 * about. It matters for the acting administrator too, not only for the target: a
 * self-grant is permitted, so an admin can widen themselves and see nothing change.
 */
const IDENTITY_WRITE: QueryKeyPrefix[] = [IDENTITY, USERS]

/**
 * A role's permission set, or which role someone holds.
 *
 * IDENTITY again, and for a reason easy to miss: granting a permission to a role
 * changes the effective permissions of every member, including the administrator
 * making the change if they happen to hold that role themselves.
 */
const ROLE_WRITE: QueryKeyPrefix[] = [IDENTITY, USERS, ROLES]

/**
 * Staffing — which applications someone is assigned to, and on which functional team.
 *
 * The widest group, because application assignments are what scope every ticket
 * collection and every analytics figure a user may read. Changing them changes not
 * only who the person is but which data they are answered with, so the collections
 * themselves are stale, not merely the identity behind them.
 */
const STAFFING_WRITE: QueryKeyPrefix[] = [IDENTITY, USERS, TICKETS, ANALYTICS]

/** A batch import creates tickets in bulk and enqueues a full graph rebuild. */
const BATCH_IMPORT_WRITE: QueryKeyPrefix[] = [TICKETS, ANALYTICS, KB_SCHEDULE]

/**
 * Marks every key beneath each prefix stale.
 *
 * Only queries with a live observer refetch immediately; the rest are flagged and
 * refetch the next time something mounts them. That is what keeps a broad group
 * cheap — adding ANALYTICS to every ticket write costs nothing while the user is on
 * the ticket page, and costs one round of refetches exactly when they are looking at
 * the Analyses page, which is when it is wanted.
 */
function invalidateGroups(queryClient: QueryClient, groups: QueryKeyPrefix[]): void {
  for (const queryKey of groups) {
    void queryClient.invalidateQueries({ queryKey })
  }
}

export {
  TICKETS,
  ANALYTICS,
  IDENTITY,
  USERS,
  ROLES,
  KB_SCHEDULE,
  TICKET_WRITE,
  IDENTITY_WRITE,
  ROLE_WRITE,
  STAFFING_WRITE,
  BATCH_IMPORT_WRITE,
  invalidateGroups,
}
export type { QueryKeyPrefix }
