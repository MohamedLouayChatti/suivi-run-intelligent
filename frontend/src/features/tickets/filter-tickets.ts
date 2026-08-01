import type { components } from "@/types/api"
import { activeStatusOptions } from "@/features/tickets/constants"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]
type Application = components["schemas"]["Application"]
type Priority = components["schemas"]["Priority"]
type Status = components["schemas"]["Status"]
type Category = components["schemas"]["Category"]

interface TicketFilters {
  search: string
  application: Application | "all"
  priority: Priority | "all"
  status: Status | "all"
  assigneeId: string | "all"
  category: Category | "all"
}

const defaultTicketFilters: TicketFilters = {
  search: "",
  application: "all",
  priority: "all",
  status: "all",
  assigneeId: "all",
  category: "all",
}

// Applies the shared filter bar to a ticket list, always scoped to the statuses that
// represent active operational work (OPEN, IN_PROGRESS, RESOLVED) — this page never
// displays CLOSED or TRANSFERRED tickets, those belong to History.
function applyTicketFilters(tickets: TicketSummary[], filters: TicketFilters): TicketSummary[] {
  return tickets.filter((t) => {
    if (!activeStatusOptions.includes(t.status)) return false
    if (filters.status !== "all" && t.status !== filters.status) return false
    if (filters.application !== "all" && t.application !== filters.application) return false
    if (filters.priority !== "all" && t.priority !== filters.priority) return false
    if (filters.category !== "all" && t.category !== filters.category) return false
    if (filters.assigneeId !== "all" && t.assignee?.id !== filters.assigneeId) return false
    if (filters.search.trim()) {
      const term = filters.search.trim().toLowerCase()
      const haystack = `${t.id} ${t.title}`.toLowerCase()
      if (!haystack.includes(term)) return false
    }
    return true
  })
}

export { applyTicketFilters, defaultTicketFilters }
export type { TicketFilters }
