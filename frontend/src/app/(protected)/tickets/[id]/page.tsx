"use client"

import { useParams } from "next/navigation"

import { PageBody } from "@/components/app/page"
import { Skeleton } from "@/components/ui/skeleton"
import { useTicketDetail } from "@/features/tickets/details/use-ticket-detail"
import { getSimilarIncidents } from "@/features/tickets/details/mock-similar-incidents"
import { useUserDirectory } from "@/hooks/use-user-directory"
import { RequirePermission, usePermissions } from "@/lib/auth"
import { TicketHeader } from "@/features/tickets/details/ticket-header"
import { DescriptionCard } from "@/features/tickets/details/description-card"
import { CommentsSection } from "@/features/tickets/details/comments-section"
import { AttachmentsSection } from "@/features/tickets/details/attachments-section"
import { ActivityTimeline } from "@/features/tickets/details/activity-timeline"
import { TicketMetadataCard } from "@/features/tickets/details/ticket-metadata-card"
import { SimilarIncidentsCard } from "@/features/tickets/details/similar-incidents-card"

export default function TicketDetailsPage() {
  const params = useParams<{ id: string }>()
  return <TicketDetailView key={params.id} id={params.id} />
}

function TicketDetailView({ id }: { id: string }) {
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
    onAddComment,
    onUploadTicketAttachment,
    onDeleteTicketAttachment,
    onDeleteCommentAttachment,
  } = useTicketDetail(id)
  const { users } = useUserDirectory()
  const { user: currentUser, hasPermission, isTicketAssignee, isAdmin } = usePermissions()

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

  const similarIncidents = getSimilarIncidents(ticket.id)

  // Mirrors Ticket.reassign's own checks (app/modules/ticket_management/domain/entities/
  // ticket.py) plus ReassignTicketHandler's (application/commands/reassign_ticket/handler.py)
  // — the backend rejects an inactive/mismatched-team/mismatched-application target, and
  // rejects reassigning to the current assignee (no-op), so the picker only offers candidates
  // that would actually be accepted.
  const reassignCandidates = users.filter(
    (u) =>
      u.active &&
      u.id !== ticket.assignee?.id &&
      u.functional_team === ticket.functional_team &&
      u.application_assignments.some((a) => a.application === ticket.application)
  )

  // Mirrors Ticket._transition_to's allowed map and the explicit checks in resume()/close()
  // (app/modules/ticket_management/domain/entities/ticket.py) — every status-changing action
  // also requires the ticket to be unarchived, since all of them go through _ensure_mutable.
  const assigneeOrAdmin = isTicketAssignee(ticket) || isAdmin
  const mutable = ticket.archived_at === null
  const canChangeStatus = mutable && hasPermission("ticket.change_status") && isTicketAssignee(ticket)
  const isResolvedOrTransferred = ticket.status === "RESOLVED" || ticket.status === "TRANSFERRED"

  return (
    <RequirePermission permission="ticket.read">
      <TicketHeader
        ticket={ticket}
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
        canReassign={mutable && ticket.status !== "CLOSED" && hasPermission("ticket.assign") && assigneeOrAdmin}
        canChangePriority={
          mutable && ticket.status !== "CLOSED" && hasPermission("ticket.change_priority") && assigneeOrAdmin
        }
        canArchive={hasPermission("ticket.archive") && assigneeOrAdmin}
        canRestore={hasPermission("ticket.restore") && assigneeOrAdmin}
        onStart={onStart}
        onResolve={onResolve}
        onResume={onResume}
        onClose={onClose}
        onArchive={onArchive}
        onRestore={onRestore}
        onReassign={onReassign}
        onChangePriority={onChangePriority}
        onTransfer={onTransfer}
      />
      <PageBody className="space-y-6">
        <div className="grid gap-6 items-start xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="min-w-0 space-y-6">
            <DescriptionCard ticket={ticket} />
            <CommentsSection
              ticket={ticket}
              isLoading={false}
              onAddComment={(content, files) => currentUser && onAddComment(currentUser.id, content, files)}
              onDeleteCommentAttachment={onDeleteCommentAttachment}
            />
            <AttachmentsSection
              ticket={ticket}
              onUploadAttachment={onUploadTicketAttachment}
              onDeleteAttachment={onDeleteTicketAttachment}
            />
            <ActivityTimeline ticket={ticket} />
          </div>
          <div className="space-y-6 xl:sticky xl:top-6">
            <TicketMetadataCard ticket={ticket} />
            <SimilarIncidentsCard incidents={similarIncidents} />
          </div>
        </div>
      </PageBody>
    </RequirePermission>
  )
}
