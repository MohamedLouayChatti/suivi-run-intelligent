"use client"

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { components } from "@/types/api"
import {
  listTickets,
  listActiveTickets,
  createTicket,
  addTicketAttachment,
  type ActiveTicketsFilters,
} from "@/services/api/tickets"
import { TICKET_WRITE, invalidateGroups } from "@/lib/cache-invalidation"

type TicketCreateRequest = components["schemas"]["TicketCreateRequest"]

const ticketsListQueryKey = ["tickets", "list"] as const

function useTicketsList() {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ticketsListQueryKey,
    queryFn: () => listTickets(),
  })

  const createMutation = useMutation({
    mutationFn: (payload: TicketCreateRequest) => createTicket(payload),
    onSuccess: () => invalidateGroups(queryClient, TICKET_WRITE),
  })

  // This had no onSuccess at all — the only mutation in the app without one. It is
  // mostly invisible because the create flow uploads before anything reads the new
  // ticket, but an attachment is a state change like any other and the ticket it
  // lands on may well already be open in another view.
  const uploadAttachmentMutation = useMutation({
    mutationFn: ({ ticketId, file }: { ticketId: string; file: File }) => addTicketAttachment(ticketId, file),
    onSuccess: () => invalidateGroups(queryClient, TICKET_WRITE),
  })

  return {
    tickets: query.data ?? [],
    isLoading: query.isPending,
    isError: query.isError,
    addTicket: createMutation.mutateAsync,
    uploadAttachment: (ticketId: string, file: File) => uploadAttachmentMutation.mutateAsync({ ticketId, file }),
  }
}

interface UseActiveTicketsParams {
  filters: ActiveTicketsFilters
  page: number
  pageSize: number
  assigneeId?: string
  excludeAssigneeId?: string
  /** False skips the request entirely rather than sending a query the caller already knows
   * is unsatisfiable — see MyActiveTicketsTable, which does this when the assignee filter
   * names someone other than the current user. */
  enabled?: boolean
}

/**
 * Backs the Tickets page's "Mes tickets actifs"/"Tickets actifs de l'équipe" tables: each
 * fetches its own server-filtered, server-paginated slice (GET /tickets, active_only=true)
 * instead of the two tables re-filtering one unfiltered, capped `useTicketsList()` page in
 * the browser. Shares `ticketsListQueryKey`'s prefix so the invalidation `useTicketDetail`
 * already does after a ticket mutation refreshes both tables the same way it refreshes
 * `useTicketsList`.
 */
function useActiveTickets({ filters, page, pageSize, assigneeId, excludeAssigneeId, enabled = true }: UseActiveTicketsParams) {
  const query = useQuery({
    queryKey: [...ticketsListQueryKey, "active", { filters, page, pageSize, assigneeId, excludeAssigneeId }] as const,
    queryFn: () => listActiveTickets({ filters, assigneeId, excludeAssigneeId, page, pageSize }),
    placeholderData: keepPreviousData,
    enabled,
  })

  return {
    tickets: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isPending && enabled,
  }
}

export { useTicketsList, useActiveTickets, ticketsListQueryKey }
