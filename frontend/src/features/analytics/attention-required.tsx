import { AlertTriangle } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { PriorityBadge } from "@/components/app/status"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { AttentionRequired } from "@/features/analytics/types"

interface AttentionRequiredSectionProps {
  data: AttentionRequired
}

function AttentionRequiredSection({ data }: AttentionRequiredSectionProps) {
  return (
    <SectionCard
      title="Nécessite une attention"
      description="Incidents ouverts au-delà du seuil habituel"
      bodyClassName="space-y-4"
    >
      <div className="flex items-center gap-3 rounded-lg border border-warning/30 bg-warning/10 p-4">
        <AlertTriangle className="size-5 shrink-0 text-warning" strokeWidth={1.75} />
        <p className="text-sm font-medium text-warning">
          {data.count} incident{data.count > 1 ? "s" : ""} ouvert{data.count > 1 ? "s" : ""} depuis
          plus de {data.thresholdDays} jours
        </p>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Ticket</TableHead>
            <TableHead>Ancienneté</TableHead>
            <TableHead>Priorité</TableHead>
            <TableHead>Assigné à</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.incidents.map((incident) => (
            <TableRow key={incident.ticketId}>
              <TableCell className="max-w-[280px] truncate font-medium" title={incident.title}>
                {incident.ticketId} · {incident.title}
              </TableCell>
              <TableCell className="tabular-nums text-muted-foreground">
                {incident.ageDays} j
              </TableCell>
              <TableCell>
                <PriorityBadge priority={incident.priority} />
              </TableCell>
              <TableCell className="text-muted-foreground">{incident.assignee}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  )
}

export { AttentionRequiredSection }
