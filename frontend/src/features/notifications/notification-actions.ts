import type { NotificationResponse } from "@/services/api/notifications"

/**
 * The backend deliberately sends a discriminator dict instead of a URL (see
 * NotificationAction in the notifications module) — routing is a frontend concern.
 * Mirrors the exact `type` discriminators from action_serialization.py.
 */
type NotificationAction =
  | { type: "open_ticket"; ticketId: string }
  | { type: "open_comment"; ticketId: string; commentId: string }
  | { type: "open_user"; userId: string }

function parseNotificationAction(action: NotificationResponse["action"]): NotificationAction | null {
  if (!action || typeof action.type !== "string") return null

  switch (action.type) {
    case "open_ticket":
      return typeof action.ticket_id === "string" ? { type: "open_ticket", ticketId: action.ticket_id } : null
    case "open_comment":
      return typeof action.ticket_id === "string" && typeof action.comment_id === "string"
        ? { type: "open_comment", ticketId: action.ticket_id, commentId: action.comment_id }
        : null
    case "open_user":
      return typeof action.user_id === "string" ? { type: "open_user", userId: action.user_id } : null
    default:
      return null
  }
}

/**
 * Where a notification's action leads. Comments aren't independently routable — the
 * ticket detail page is the only place they render — so `open_comment` lands on the
 * same ticket page as `open_ticket`. `open_user` has no per-user route, only the
 * admin users list, so it deep-links there via `?highlight=` (read by UsersTable).
 */
function resolveNotificationHref(action: NotificationAction): string {
  switch (action.type) {
    case "open_ticket":
    case "open_comment":
      return `/tickets/${action.ticketId}`
    case "open_user":
      return `/admin/users?highlight=${action.userId}`
  }
}

export { parseNotificationAction, resolveNotificationHref }
export type { NotificationAction }
