import { SectionCard } from "@/components/app/page"
import { statusConfig } from "@/components/app/status"
import { Progress } from "@/components/ui/progress"
import type { components } from "@/types/api"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]
type Status = components["schemas"]["Status"]

const statusOrder: Status[] = ["OPEN", "IN_PROGRESS", "RESOLVED", "TRANSFERRED", "CLOSED"]

interface TicketStatusSummaryProps {
  tickets: TicketSummary[]
}

function TicketStatusSummary({ tickets }: TicketStatusSummaryProps) {
  const total = tickets.length || 1

  return (
    <SectionCard title="Répartition de mes tickets" description="Tous statuts confondus">
      <div className="space-y-5">
        {statusOrder.map((status) => {
          const { label } = statusConfig[status]
          const count = tickets.filter((t) => t.status === status).length
          return (
            <div key={status}>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{label}</span>
                <span className="font-medium tabular-nums">{count}</span>
              </div>
              <Progress value={(count / total) * 100} />
            </div>
          )
        })}
      </div>
    </SectionCard>
  )
}

export { TicketStatusSummary }
