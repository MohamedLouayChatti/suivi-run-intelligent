import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

interface ActivityEvent {
  id: string
  label: string
  timestamp: string
}

// Derives a lifecycle timeline from the ticket's own timestamps, since no domain-event feed
// is exposed to the frontend yet. Once Ticket Management events (TicketCreated,
// TicketStatusChanged, …) are surfaced through an API, this can be replaced with a direct
// events fetch — consumers only depend on ActivityEvent[].
function buildActivityTimeline(ticket: TicketDetail): ActivityEvent[] {
  const events: ActivityEvent[] = [
    { id: "created", label: "Ticket créé", timestamp: ticket.created_at },
  ]

  if (ticket.status === "IN_PROGRESS" || ticket.status === "RESOLVED" || ticket.status === "CLOSED") {
    events.push({ id: "started", label: "Statut changé vers En cours", timestamp: ticket.created_at })
  }

  if (ticket.transferred_to) {
    events.push({
      id: "transferred",
      label: `Transféré vers ${ticket.transferred_to}`,
      timestamp: ticket.updated_at,
    })
  }

  if (ticket.resolved_at) {
    events.push({ id: "resolved", label: "Ticket résolu", timestamp: ticket.resolved_at })
  }

  if (ticket.closed_at) {
    events.push({ id: "closed", label: "Ticket clôturé", timestamp: ticket.closed_at })
  }

  if (ticket.archived_at) {
    events.push({ id: "archived", label: "Ticket archivé", timestamp: ticket.archived_at })
  }

  return events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
}

export { buildActivityTimeline }
export type { ActivityEvent }
