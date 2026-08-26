"use client"

import { useParams, useSearchParams } from "next/navigation"

import { PageBody } from "@/components/app/page"
import { Skeleton } from "@/components/ui/skeleton"
import { useTicketDetail } from "@/features/tickets/details/use-ticket-detail"
import { useSimilarIncidents } from "@/features/tickets/details/use-similar-incidents"
import { useUserDirectory } from "@/hooks/use-user-directory"
import { RequireRouteAccess, usePermissions } from "@/lib/auth"
import { TicketHeader } from "@/features/tickets/details/ticket-header"
import { DescriptionCard } from "@/features/tickets/details/description-card"
import { ResolutionCard } from "@/features/tickets/details/resolution-card"
import { CommentsSection } from "@/features/tickets/details/comments-section"
import { AttachmentsSection } from "@/features/tickets/details/attachments-section"
import { ActivityTimeline } from "@/features/tickets/details/activity-timeline"
import { TicketMetadataCard } from "@/features/tickets/details/ticket-metadata-card"
import { SimilarIncidentsCard } from "@/features/tickets/details/similar-incidents-card"

export default function TicketDetailsPage() {
  const params = useParams<{ id: string }>()
  // `from` is set by the similar-incidents card when one ticket is opened from another's
  // suggestions; absent for every other way of reaching this page.
  const fromTicketId = useSearchParams().get("from")
  return <TicketDetailView key={params.id} id={params.id} fromTicketId={fromTicketId} />
}

function TicketDetailView({ id, fromTicketId }: { id: string; fromTicketId: string | null }) {
  const {
    ticket,
    isLoading,
    notFound,
    onStart,
    onResolve,
    onClose,
    onResume,
    onArchive,
    onRestore,
    onReassign,
    onChangePriority,
    onTransfer,
    onUpdateJira,
    onUpdateOperationalHighlight,
    onAddComment,
    onEditComment,
    onDeleteComment,
    onUploadTicketAttachment,
    onDeleteTicketAttachment,
    onDeleteCommentAttachment,
    ticketAttachmentError,
    commentAttachmentError,
  } = useTicketDetail(id)
  const { users } = useUserDirectory()
  const {
    incidents: similarIncidents,
    isLoading: isLoadingSimilarIncidents,
    isError: similarIncidentsFailed,
  } = useSimilarIncidents(id)
  const { user: currentUser, hasPermission, isTicketAssignee, canManageOthersTickets } = usePermissions()

  if (isLoading) {
    return (
      <PageBody className="space-y-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid gap-6 items-start xl:grid-cols-[minmax(0,1fr)_380px]">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </PageBody>
    )
  }

  if (notFound || !ticket) {
    return (
      <PageBody>
        <p className="text-sm text-muted-foreground">Ticket introuvable.</p>
      </PageBody>
    )
  }

  // Mirrors Ticket.reassign's own checks (app/modules/ticket_management/domain/entities/
  // ticket.py) plus ReassignTicketHandler's (application/commands/reassign_ticket/handler.py)
  // — the backend rejects an inactive/mismatched-team/mismatched-application target, and
  // rejects reassigning to the current assignee (no-op), so the picker only offers candidates
  // that would actually be accepted. A read-only assignment grants reach without staffing, so
  // it does not qualify a candidate here — only a primary/backup assignment describes someone
  // actually working the application.
  const reassignCandidates = users.filter(
    (u) =>
      u.active &&
      u.id !== ticket.assignee?.id &&
      u.functional_team === ticket.functional_team &&
      u.application_assignments.some(
        (a) => a.application === ticket.application && a.assignment_type !== "READ_ONLY"
      )
  )

  // Mirrors Ticket._transition_to's allowed map and the explicit checks in resume()/close()
  // (app/modules/ticket_management/domain/entities/ticket.py) — every status-changing action
  // also requires the ticket to be unarchived, since all of them go through _ensure_mutable.
  // Mirrors TicketAccessPolicy's _ASSIGNEE_OR_MANAGER_OPERATIONS: the assignee, or anyone whose
  // permissions widen that to tickets they are not assigned to — everywhere, or within the one
  // application they run.
  const canManage = isTicketAssignee(ticket) || canManageOthersTickets(ticket.application)
  const mutable = ticket.archived_at === null
  const canChangeStatus = mutable && hasPermission("ticket.change_status") && isTicketAssignee(ticket)
  const isResolvedOrTransferred = ticket.status === "RESOLVED" || ticket.status === "TRANSFERRED"

  return (
    <RequireRouteAccess href="/tickets">
      <TicketHeader
        ticket={ticket}
        fromTicketId={fromTicketId}
        users={reassignCandidates}
        canStart={canChangeStatus && ticket.status === "OPEN"}
        canResolve={canChangeStatus && ticket.status === "IN_PROGRESS"}
        canResume={canChangeStatus && isResolvedOrTransferred}
        canClose={canChangeStatus && isResolvedOrTransferred}
        canTransfer={
          mutable &&
          hasPermission("ticket.transfer_application") &&
          isTicketAssignee(ticket) &&
          ticket.status === "IN_PROGRESS"
        }
        canReassign={mutable && ticket.status !== "CLOSED" && hasPermission("ticket.assign") && canManage}
        canChangePriority={
          mutable && ticket.status !== "CLOSED" && hasPermission("ticket.change_priority") && canManage
        }
        canManageJira={mutable && ticket.status !== "CLOSED" && hasPermission("ticket.manage_jira") && canManage}
        canManageHighlight={
          mutable && ticket.status !== "CLOSED" && hasPermission("ticket.manage_highlight") && canManage
        }
        canArchive={hasPermission("ticket.archive") && canManage}
        canRestore={hasPermission("ticket.restore") && canManage}
        onStart={onStart}
        onResolve={onResolve}
        onResume={onResume}
        onClose={onClose}
        onArchive={onArchive}
        onRestore={onRestore}
        onReassign={onReassign}
        onChangePriority={onChangePriority}
        onTransfer={onTransfer}
        onUpdateJira={onUpdateJira}
        onUpdateOperationalHighlight={onUpdateOperationalHighlight}
      />
      <PageBody className="space-y-6">
        <div className="grid gap-6 items-start xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="min-w-0 space-y-6">
            <DescriptionCard ticket={ticket} />
            <ResolutionCard ticket={ticket} />
            <CommentsSection
              ticket={ticket}
              isLoading={false}
              onAddComment={(content, files) => currentUser && onAddComment(currentUser.id, content, files)}
              onEditComment={onEditComment}
              onDeleteComment={onDeleteComment}
              onDeleteCommentAttachment={onDeleteCommentAttachment}
              attachmentError={commentAttachmentError}
            />
            <AttachmentsSection
              ticket={ticket}
              onUploadAttachment={onUploadTicketAttachment}
              onDeleteAttachment={onDeleteTicketAttachment}
              error={ticketAttachmentError}
            />
            <ActivityTimeline ticket={ticket} />
          </div>
          <div className="space-y-6 xl:sticky xl:top-6">
            <TicketMetadataCard ticket={ticket} />
            <SimilarIncidentsCard
              incidents={similarIncidents}
              isLoading={isLoadingSimilarIncidents}
              isError={similarIncidentsFailed}
              sourceTicketId={ticket.id}
            />
          </div>
        </div>
      </PageBody>
    </RequireRouteAccess>
  )
}
