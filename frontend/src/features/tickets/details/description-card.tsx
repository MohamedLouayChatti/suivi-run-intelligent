import { SectionCard } from "@/components/app/page"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

function DescriptionCard({ ticket }: { ticket: TicketDetail }) {
  return (
    <SectionCard title="Description">
      <p className="text-sm whitespace-pre-wrap text-foreground">{ticket.description}</p>
    </SectionCard>
  )
}

export { DescriptionCard }
