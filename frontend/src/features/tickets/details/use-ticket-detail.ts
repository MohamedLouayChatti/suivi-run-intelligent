"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import type { components } from "@/types/api"
import {
  getTicket,
  startTicket,
  resolveTicket,
  closeTicket,
  resumeTicket,
  transferTicket,
  reassignTicket,
  changeTicketPriority,
  updateTicketJira,
  updateOperationalHighlight,
  archiveTicket,
  restoreTicket,
  addComment,
  addTicketAttachment,
  editComment,
  deleteComment,
  addCommentAttachment,
  deleteTicketAttachment,
  deleteCommentAttachment,
} from "@/services/api/tickets"
import { TICKET_WRITE, invalidateGroups } from "@/lib/cache-invalidation"

type Priority = components["schemas"]["Priority"]
type TransferDestination = components["schemas"]["TransferDestination"]
type JiraDetailsUpdateRequest = components["schemas"]["JiraDetailsUpdateRequest"]

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

  // The three keys this used to name individually all live under ["tickets", ...],
  // so the group's own prefix reaches this ticket's detail, both list views and the
  // history table in one. What it adds is the analytics half: every figure on the
  // Analyses page and both Dashboard widgets are computed from the columns these
  // mutations write, and nothing invalidated them before.
  function afterMutation() {
    invalidateGroups(queryClient, TICKET_WRITE)
  }

  const start = useMutation({ mutationFn: () => startTicket(id), onSuccess: afterMutation })
  const resolve = useMutation({
    mutationFn: (resolutionNotes: string) => resolveTicket(id, resolutionNotes),
    onSuccess: afterMutation,
  })
  const close = useMutation({ mutationFn: () => closeTicket(id), onSuccess: afterMutation })
  const resume = useMutation({ mutationFn: () => resumeTicket(id), onSuccess: afterMutation })
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
  const updateJira = useMutation({
    mutationFn: (payload: JiraDetailsUpdateRequest) => updateTicketJira(id, payload),
    onSuccess: afterMutation,
  })
  const updateHighlight = useMutation({
    mutationFn: (operationalHighlight: boolean) => updateOperationalHighlight(id, operationalHighlight),
    onSuccess: afterMutation,
  })
  const archive = useMutation({ mutationFn: () => archiveTicket(id), onSuccess: afterMutation })
  const restore = useMutation({ mutationFn: () => restoreTicket(id), onSuccess: afterMutation })
  const addTicketComment = useMutation({
    mutationFn: async ({ authorId, content, files }: { authorId: string; content: string; files: File[] }) => {
      const result = await addComment(id, authorId, content)
      const newComment = result.comments[result.comments.length - 1]
      let updated = result
      for (const file of files) {
        updated = await addCommentAttachment(id, newComment.id, file)
      }
      return updated
    },
    onSuccess: afterMutation,
  })
  const uploadTicketAttachmentMutation = useMutation({
    mutationFn: (file: File) => addTicketAttachment(id, file),
    onSuccess: afterMutation,
  })
  const deleteTicketAttachmentMutation = useMutation({
    mutationFn: (attachmentId: string) => deleteTicketAttachment(id, attachmentId),
    onSuccess: afterMutation,
  })
  const editCommentMutation = useMutation({
    mutationFn: ({ commentId, content }: { commentId: string; content: string }) =>
      editComment(id, commentId, content),
    onSuccess: afterMutation,
  })
  const deleteCommentMutation = useMutation({
    mutationFn: (commentId: string) => deleteComment(id, commentId),
    onSuccess: afterMutation,
  })
  const deleteCommentAttachmentMutation = useMutation({
    mutationFn: ({ commentId, attachmentId }: { commentId: string; attachmentId: string }) =>
      deleteCommentAttachment(id, commentId, attachmentId),
    onSuccess: afterMutation,
  })

  return {
    ticket: query.data ?? null,
    isLoading: query.isPending,
    notFound: query.isError,
    onStart: () => start.mutate(),
    onResolve: (resolutionNotes: string) => resolve.mutate(resolutionNotes),
    onClose: () => close.mutate(),
    onResume: () => resume.mutate(),
    onTransfer: (destination: TransferDestination) => transfer.mutate(destination),
    onReassign: (assigneeId: string) => reassign.mutate(assigneeId),
    onChangePriority: (priority: Priority) => changePriority.mutate(priority),
    onUpdateJira: (payload: JiraDetailsUpdateRequest) => updateJira.mutate(payload),
    onUpdateOperationalHighlight: (operationalHighlight: boolean) => updateHighlight.mutate(operationalHighlight),
    onArchive: () => archive.mutate(),
    onRestore: () => restore.mutate(),
    onAddComment: (authorId: string, content: string, files: File[]) =>
      addTicketComment.mutate({ authorId, content, files }),
    onUploadTicketAttachment: (file: File) => uploadTicketAttachmentMutation.mutate(file),
    onDeleteTicketAttachment: (attachmentId: string) => deleteTicketAttachmentMutation.mutate(attachmentId),
    onEditComment: (commentId: string, content: string) =>
      editCommentMutation.mutate({ commentId, content }),
    onDeleteComment: (commentId: string) => deleteCommentMutation.mutate(commentId),
    onDeleteCommentAttachment: (commentId: string, attachmentId: string) =>
      deleteCommentAttachmentMutation.mutate({ commentId, attachmentId }),
    ticketAttachmentError: uploadTicketAttachmentMutation.error?.message ?? deleteTicketAttachmentMutation.error?.message ?? null,
    commentAttachmentError: addTicketComment.error?.message ?? deleteCommentAttachmentMutation.error?.message ?? null,
    commentError: editCommentMutation.error?.message ?? deleteCommentMutation.error?.message ?? null,
  }
}

export { useTicketDetail }
