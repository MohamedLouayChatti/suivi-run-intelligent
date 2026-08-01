"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { components } from "@/types/api"
import {
  getTicket,
  startTicket,
  resolveTicket,
  transferTicket,
  reassignTicket,
  changeTicketPriority,
  archiveTicket,
  restoreTicket,
  addComment,
} from "@/services/api/tickets"
import { ticketsListQueryKey } from "@/features/tickets/use-tickets-list"

type Priority = components["schemas"]["Priority"]
type TransferDestination = components["schemas"]["TransferDestination"]

function ticketDetailQueryKey(id: string) {
  return ["tickets", "detail", id] as const
}

function useTicketDetail(id: string) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ticketDetailQueryKey(id),
    queryFn: () => getTicket(id),
    retry: false,
  })

  function afterMutation() {
    queryClient.invalidateQueries({ queryKey: ticketDetailQueryKey(id) })
    queryClient.invalidateQueries({ queryKey: ticketsListQueryKey })
  }

  const start = useMutation({ mutationFn: () => startTicket(id), onSuccess: afterMutation })
  const resolve = useMutation({
    mutationFn: (resolutionNotes: string) => resolveTicket(id, resolutionNotes),
    onSuccess: afterMutation,
  })
  const transfer = useMutation({
    mutationFn: (destination: TransferDestination) => transferTicket(id, destination),
    onSuccess: afterMutation,
  })
  const reassign = useMutation({
    mutationFn: (assigneeId: string) => reassignTicket(id, assigneeId),
    onSuccess: afterMutation,
  })
  const changePriority = useMutation({
    mutationFn: (priority: Priority) => changeTicketPriority(id, priority),
    onSuccess: afterMutation,
  })
  const archive = useMutation({ mutationFn: () => archiveTicket(id), onSuccess: afterMutation })
  const restore = useMutation({ mutationFn: () => restoreTicket(id), onSuccess: afterMutation })
  const addTicketComment = useMutation({
    mutationFn: ({ authorId, content }: { authorId: string; content: string }) =>
      addComment(id, authorId, content),
    onSuccess: afterMutation,
  })

  return {
    ticket: query.data ?? null,
    isLoading: query.isPending,
    notFound: query.isError,
    onStart: () => start.mutate(),
    onResolve: (resolutionNotes: string) => resolve.mutate(resolutionNotes),
    onTransfer: (destination: TransferDestination) => transfer.mutate(destination),
    onReassign: (assigneeId: string) => reassign.mutate(assigneeId),
    onChangePriority: (priority: Priority) => changePriority.mutate(priority),
    onArchive: () => archive.mutate(),
    onRestore: () => restore.mutate(),
    onAddComment: (authorId: string, content: string) => addTicketComment.mutate({ authorId, content }),
  }
}

export { useTicketDetail }
