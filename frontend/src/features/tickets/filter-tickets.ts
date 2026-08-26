import type { components } from "@/types/api"

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

/** The filter bar defaults to the user's primary application rather than "all" — pass
 * it in once the current user's profile (GET /auth/me) has resolved. */
function createDefaultTicketFilters(primaryApplication: Application): TicketFilters {
  return { ...defaultTicketFilters, application: primaryApplication }
}

export { defaultTicketFilters, createDefaultTicketFilters }
export type { TicketFilters }
