"use client"

import { useQuery } from "@tanstack/react-query"

import { listTickets } from "@/services/api/tickets"
import { ticketsListQueryKey } from "@/features/tickets/use-tickets-list"

// History shares the exact same "all tickets" data source as the Tickets page (GET /tickets
// only filters by status client-side via filter-history.ts), so it reuses the same query key
// — TanStack Query dedupes the request when both pages' data is already cached.
function useHistoryList() {
  const query = useQuery({
    queryKey: ticketsListQueryKey,
    queryFn: () => listTickets(),
  })

  return { tickets: query.data ?? [], isLoading: query.isPending, isError: query.isError }
}

export { useHistoryList }
