import { PageHeader } from "@/components/app/page"
import { TicketActions } from "@/features/tickets/details/ticket-actions"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type Priority = components["schemas"]["Priority"]
type TransferDestination = components["schemas"]["TransferDestination"]
type UserSummary = components["schemas"]["UserDirectoryResponse"]
type JiraDetailsUpdateRequest = components["schemas"]["JiraDetailsUpdateRequest"]

interface TicketHeaderProps {
  ticket: TicketDetail
  users: UserSummary[]
  canStart: boolean
  canResolve: boolean
  canResume: boolean
  canClose: boolean
  canTransfer: boolean
  canReassign: boolean
  canChangePriority: boolean
  canManageJira: boolean
  canManageHighlight: boolean
  canArchive: boolean
  canRestore: boolean
  onStart: () => void
  onResolve: (resolutionNotes: string) => void
  onResume: () => void
  onClose: () => void
  onArchive: () => void
  onRestore: () => void
  onReassign: (assigneeId: string) => void
  onChangePriority: (priority: Priority) => void
  onTransfer: (destination: TransferDestination) => void
  onUpdateJira: (payload: JiraDetailsUpdateRequest) => void
  onUpdateOperationalHighlight: (operationalHighlight: boolean) => void
}

function TicketHeader(props: TicketHeaderProps) {
  const { ticket } = props

  return (
    <PageHeader
      title={ticket.title}
      description={<span className="font-mono text-xs">{ticket.id}</span>}
      breadcrumbs={[{ label: "Tickets", href: "/tickets" }, { label: ticket.id.slice(0, 8) }]}
      actions={<TicketActions {...props} />}
    />
  )
}

export { TicketHeader }
