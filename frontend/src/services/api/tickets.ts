import type { components } from "@/types/api"

import { httpClient } from "./client"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]
type TicketDetail = components["schemas"]["TicketDetailResponse"]
type TicketCreateRequest = components["schemas"]["TicketCreateRequest"]
type Priority = components["schemas"]["Priority"]
type TransferDestination = components["schemas"]["TransferDestination"]
type JiraDetailsUpdateRequest = components["schemas"]["JiraDetailsUpdateRequest"]

/**
 * The list endpoint only accepts page/page_size — the richer filter fields on the
 * backend's ListTicketsQuery (status, priority, application, ...) are never read from
 * the request, so callers filter/sort the fetched page client-side (see filter-tickets.ts
 * / filter-history.ts) rather than passing them here.
 */
async function listTickets(pageSize = 100): Promise<TicketSummary[]> {
  const { data } = await httpClient.get<TicketSummary[]>("/tickets", {
    params: { page: 1, page_size: pageSize },
  })
  return data
}

async function getTicket(ticketId: string): Promise<TicketDetail> {
  const { data } = await httpClient.get<TicketDetail>(`/tickets/${ticketId}`)
  return data
}

async function createTicket(payload: TicketCreateRequest): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>("/tickets", payload)
  return data
}

async function startTicket(ticketId: string): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/start`)
  return data
}

async function resolveTicket(ticketId: string, resolutionNotes: string): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/resolve`, {
    resolution_notes: resolutionNotes,
  })
  return data
}

async function closeTicket(ticketId: string): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/close`)
  return data
}

async function resumeTicket(ticketId: string): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/resume`)
  return data
}

async function transferTicket(ticketId: string, destination: TransferDestination): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/transfer`, {
    transferred_to: destination,
  })
  return data
}

async function reassignTicket(ticketId: string, assigneeId: string): Promise<TicketDetail> {
  const { data } = await httpClient.patch<TicketDetail>(`/tickets/${ticketId}/assignee`, {
    assignee_id: assigneeId,
  })
  return data
}

async function changeTicketPriority(ticketId: string, priority: Priority): Promise<TicketDetail> {
  const { data } = await httpClient.patch<TicketDetail>(`/tickets/${ticketId}/priority`, { priority })
  return data
}

async function updateTicketJira(ticketId: string, payload: JiraDetailsUpdateRequest): Promise<TicketDetail> {
  const { data } = await httpClient.patch<TicketDetail>(`/tickets/${ticketId}/jira`, payload)
  return data
}

async function updateOperationalHighlight(ticketId: string, operationalHighlight: boolean): Promise<TicketDetail> {
  const { data } = await httpClient.patch<TicketDetail>(`/tickets/${ticketId}/operational-highlight`, {
    operational_highlight: operationalHighlight,
  })
  return data
}

async function archiveTicket(ticketId: string): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/archive`)
  return data
}

async function restoreTicket(ticketId: string): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/restore`)
  return data
}

async function addComment(ticketId: string, authorId: string, content: string): Promise<TicketDetail> {
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/comments`, {
    author_id: authorId,
    content,
  })
  return data
}

async function editComment(ticketId: string, commentId: string, content: string): Promise<TicketDetail> {
  const { data } = await httpClient.patch<TicketDetail>(`/comments/${commentId}`, { content }, {
    params: { ticket_id: ticketId },
  })
  return data
}

async function deleteComment(ticketId: string, commentId: string): Promise<void> {
  await httpClient.delete(`/comments/${commentId}`, { params: { ticket_id: ticketId } })
}

async function addTicketAttachment(ticketId: string, file: File): Promise<TicketDetail> {
  const formData = new FormData()
  formData.append("file", file)
  const { data } = await httpClient.post<TicketDetail>(`/tickets/${ticketId}/attachments`, formData)
  return data
}

async function addCommentAttachment(ticketId: string, commentId: string, file: File): Promise<TicketDetail> {
  const formData = new FormData()
  formData.append("file", file)
  const { data } = await httpClient.post<TicketDetail>(
    `/tickets/${ticketId}/comments/${commentId}/attachments`,
    formData,
  )
  return data
}

async function deleteTicketAttachment(ticketId: string, attachmentId: string): Promise<void> {
  await httpClient.delete(`/attachments/${attachmentId}`, { params: { ticket_id: ticketId } })
}

async function deleteCommentAttachment(ticketId: string, commentId: string, attachmentId: string): Promise<void> {
  await httpClient.delete(`/comments/${commentId}/attachments/${attachmentId}`, {
    params: { ticket_id: ticketId },
  })
}

async function downloadAttachment(attachmentId: string): Promise<Blob> {
  const { data } = await httpClient.get<Blob>(`/attachments/${attachmentId}`, { responseType: "blob" })
  return data
}

interface HistoryExportFilters {
  search: string
  application: components["schemas"]["Application"] | "all"
  status: components["schemas"]["Status"] | "all"
  assigneeId: string | "all"
  category: components["schemas"]["Category"] | "all"
  dateFrom: string
  dateTo: string
}

/** Exports the History page's currently active filters as a CSV, matching what's on screen. */
async function exportTicketHistory(filters: HistoryExportFilters): Promise<Blob> {
  const { data } = await httpClient.get<Blob>("/tickets/history/export", {
    responseType: "blob",
    params: {
      application: filters.application === "all" ? undefined : filters.application,
      status: filters.status === "all" ? undefined : filters.status,
      category: filters.category === "all" ? undefined : filters.category,
      assignee_id: filters.assigneeId === "all" ? undefined : filters.assigneeId,
      search: filters.search.trim() || undefined,
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined,
    },
  })
  return data
}

export {
  listTickets,
  getTicket,
  createTicket,
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
  downloadAttachment,
  exportTicketHistory,
}
