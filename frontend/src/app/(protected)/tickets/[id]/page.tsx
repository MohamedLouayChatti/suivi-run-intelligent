"use client"

import { useParams } from "next/navigation"

import { PageBody } from "@/components/app/page"
import { Skeleton } from "@/components/ui/skeleton"
import { useTicketDetail } from "@/features/tickets/details/use-ticket-detail"
import { getSimilarIncidents } from "@/features/tickets/details/mock-similar-incidents"
import { useUsersList } from "@/hooks/use-users-list"
import { useCurrentUser } from "@/lib/auth"
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
    onArchive,
    onRestore,
    onReassign,
    onChangePriority,
    onTransfer,
    onAddComment,
  } = useTicketDetail(id)
  const { users } = useUsersList()
  const { data: currentUser } = useCurrentUser()

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

  return (
    <>
      <TicketHeader
        ticket={ticket}
        users={users}
        onStart={onStart}
        onResolve={() => {
          const notes = window.prompt("Notes de résolution")
          if (notes) onResolve(notes)
        }}
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
              onAddComment={(content) => currentUser && onAddComment(currentUser.id, content)}
            />
            <AttachmentsSection ticket={ticket} />
            <ActivityTimeline ticket={ticket} />
          </div>
          <div className="space-y-6 xl:sticky xl:top-6">
            <TicketMetadataCard ticket={ticket} />
            <SimilarIncidentsCard incidents={similarIncidents} />
          </div>
        </div>
      </PageBody>
    </>
  )
}
