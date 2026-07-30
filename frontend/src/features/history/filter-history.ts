import type { components } from "@/types/api"
import { completedStatusOptions } from "@/features/tickets/constants"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type Application = components["schemas"]["Application"]
type Status = components["schemas"]["Status"]
type Category = components["schemas"]["Category"]

interface HistoryFilters {
  search: string
  application: Application | "all"
  status: Status | "all"
  assigneeId: string | "all"
  category: Category | "all"
  dateFrom: string
  dateTo: string
}

const defaultHistoryFilters: HistoryFilters = {
  search: "",
  application: "all",
  status: "all",
  assigneeId: "all",
  category: "all",
  dateFrom: "",
  dateTo: "",
}

// Tickets have no dedicated "transferred_at" field, so the completion moment is the
// closing timestamp when available, falling back to the last update (set alongside the
// status transition for TRANSFERRED tickets).
function getCompletedAt(ticket: TicketDetail): string {
  return ticket.closed_at ?? ticket.updated_at
}

// Applies the shared filter bar to a ticket list, always scoped to the statuses that
// represent completed work (CLOSED, TRANSFERRED) — History never displays active tickets,
// those belong to the Tickets page.
function applyHistoryFilters(tickets: TicketDetail[], filters: HistoryFilters): TicketDetail[] {
  return tickets
    .filter((t) => {
      if (!completedStatusOptions.includes(t.status)) return false
      if (filters.status !== "all" && t.status !== filters.status) return false
      if (filters.application !== "all" && t.application !== filters.application) return false
      if (filters.category !== "all" && t.category !== filters.category) return false
      if (filters.assigneeId !== "all" && t.assignee?.id !== filters.assigneeId) return false
      if (filters.search.trim()) {
        const term = filters.search.trim().toLowerCase()
        const haystack = `${t.id} ${t.title}`.toLowerCase()
        if (!haystack.includes(term)) return false
      }
      const completedAt = new Date(getCompletedAt(t))
      if (filters.dateFrom && completedAt < new Date(`${filters.dateFrom}T00:00:00`)) return false
      if (filters.dateTo && completedAt > new Date(`${filters.dateTo}T23:59:59`)) return false
      return true
    })
    .sort((a, b) => new Date(getCompletedAt(b)).getTime() - new Date(getCompletedAt(a)).getTime())
}

export { applyHistoryFilters, defaultHistoryFilters, getCompletedAt }
export type { HistoryFilters }
