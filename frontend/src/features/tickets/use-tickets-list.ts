"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { components } from "@/types/api"
import { listTickets, createTicket, addTicketAttachment } from "@/services/api/tickets"

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

  const uploadAttachmentMutation = useMutation({
    mutationFn: ({ ticketId, file }: { ticketId: string; file: File }) => addTicketAttachment(ticketId, file),
  })

  return {
    tickets: query.data ?? [],
    isLoading: query.isPending,
    isError: query.isError,
    addTicket: createMutation.mutateAsync,
    uploadAttachment: (ticketId: string, file: File) => uploadAttachmentMutation.mutateAsync({ ticketId, file }),
  }
}

export { useTicketsList, ticketsListQueryKey }
