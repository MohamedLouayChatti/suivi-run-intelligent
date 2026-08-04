import type { components } from "@/types/api"
import { completedStatusOptions } from "@/features/tickets/constants"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]
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

/** The filter bar defaults to the user's primary application rather than "all" — pass
 * it in once the current user's profile (GET /auth/me) has resolved. */
function createDefaultHistoryFilters(primaryApplication: Application): HistoryFilters {
  return { ...defaultHistoryFilters, application: primaryApplication }
}

// TicketSummaryResponse (the only shape GET /tickets returns) has no closed_at/transferred_at
// field — updated_at is set alongside the CLOSED/TRANSFERRED status transition itself, so it's
// the completion moment for every row here.
function getCompletedAt(ticket: TicketSummary): string {
  return ticket.updated_at
}

// Applies the shared filter bar to a ticket list, always scoped to the statuses that
// represent completed work (CLOSED, TRANSFERRED) — History never displays active tickets,
// those belong to the Tickets page.
function applyHistoryFilters(tickets: TicketSummary[], filters: HistoryFilters): TicketSummary[] {
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

export { applyHistoryFilters, defaultHistoryFilters, createDefaultHistoryFilters, getCompletedAt }
export type { HistoryFilters }
