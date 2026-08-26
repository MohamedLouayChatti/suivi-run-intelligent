import type { components } from "@/types/api"

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

export { defaultHistoryFilters, createDefaultHistoryFilters, getCompletedAt }
export type { HistoryFilters }
