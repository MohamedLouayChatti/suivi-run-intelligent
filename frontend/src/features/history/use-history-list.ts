"use client"

import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { listTicketHistory } from "@/services/api/tickets"
import type { HistoryFilters } from "@/features/history/filter-history"

const historyListQueryKey = ["tickets", "history"] as const

interface UseHistoryListParams {
  filters: HistoryFilters
  page: number
  pageSize: number
}

/**
 * Server-side filtered and paginated (GET /tickets/history), unlike the old useHistoryList
 * that fetched one unfiltered, capped GET /tickets page and filtered/paginated it in the
 * browser — which is what made selecting e.g. an application filter show only however many
 * of that application's tickets happened to fall inside that capped page, instead of all of
 * them.
 */
function useHistoryList({ filters, page, pageSize }: UseHistoryListParams) {
  const query = useQuery({
    queryKey: [...historyListQueryKey, { filters, page, pageSize }] as const,
    queryFn: () => listTicketHistory({ filters, page, pageSize }),
    placeholderData: keepPreviousData,
  })

  return {
    tickets: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isPending,
  }
}

export { useHistoryList, historyListQueryKey }
