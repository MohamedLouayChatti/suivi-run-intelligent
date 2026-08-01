"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { components } from "@/types/api"
import { listTickets, createTicket } from "@/services/api/tickets"

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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ticketsListQueryKey }),
  })

  return {
    tickets: query.data ?? [],
    isLoading: query.isPending,
    isError: query.isError,
    addTicket: createMutation.mutateAsync,
  }
}

export { useTicketsList, ticketsListQueryKey }
