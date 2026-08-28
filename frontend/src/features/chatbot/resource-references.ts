/**
 * The assistant marks a ticket it retrieved as an ordinary Markdown link whose target is
 * `ticket:<uuid>` (see resource_references.py, which also strips any reference the run's own tool
 * results cannot vouch for before the message is stored). The backend names *what* is referenced
 * and never *where it lives* — routing is a frontend concern here exactly as it is for a
 * notification's action, so this file is the chat counterpart of `resolveNotificationHref`.
 */

const REFERENCE_PREFIX = "ticket:"

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

/**
 * The ticket id behind a reference target, or `null` for any other href. Re-validates the id
 * rather than trusting the prefix: while an answer is still streaming this runs on half-arrived
 * text, so a target is routinely seen mid-word before its closing paren completes it.
 */
function parseTicketReference(href: string | undefined): string | null {
  if (!href || !href.startsWith(REFERENCE_PREFIX)) return null
  const ticketId = href.slice(REFERENCE_PREFIX.length)
  return UUID_PATTERN.test(ticketId) ? ticketId.toLowerCase() : null
}

function resolveTicketReferenceHref(ticketId: string): string {
  return `/tickets/${ticketId}`
}

export { parseTicketReference, resolveTicketReferenceHref }
