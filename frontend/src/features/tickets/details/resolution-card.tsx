import { CheckCircle2 } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
})

function ResolutionCard({ ticket }: { ticket: TicketDetail }) {
  if (!ticket.resolution_notes) return null

  return (
    <SectionCard
      title="Résolution"
      description={ticket.resolved_at ? `Résolu le ${dateTimeFormatter.format(new Date(ticket.resolved_at))}` : undefined}
    >
      <div className="flex items-start gap-2">
        <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />
        <p className="text-sm whitespace-pre-wrap text-foreground">{ticket.resolution_notes}</p>
      </div>
      {ticket.closed_at && (
        <p className="mt-3 text-xs text-muted-foreground">
          Ticket fermé le {dateTimeFormatter.format(new Date(ticket.closed_at))}
        </p>
      )}
    </SectionCard>
  )
}

export { ResolutionCard }
