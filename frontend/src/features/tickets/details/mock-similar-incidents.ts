import { mockTickets } from "@/features/tickets/mock-data"
import type { components } from "@/types/api"

type Status = components["schemas"]["Status"]

interface SimilarIncident {
  id: string
  title: string
  status: Status
  similarity: number
}

// Placeholder for the future Incident Intelligence semantic-search module. Replace with a
// real services/api call once it exists — consumers only depend on SimilarIncident[], so
// swapping the source is a one-line change. Returns 0-3 incidents so every state (empty,
// partial, full) can be exercised without a real similarity search.
function getSimilarIncidents(ticketId: string): SimilarIncident[] {
  const index = mockTickets.findIndex((t) => t.id === ticketId)
  if (index === -1) return []

  const count = index % 4
  const pool = mockTickets.filter((t) => t.id !== ticketId)

  return pool.slice(0, count).map((t, i) => ({
    id: t.id,
    title: t.title,
    status: t.status,
    similarity: 91 - i * 12,
  }))
}

export { getSimilarIncidents }
export type { SimilarIncident }
