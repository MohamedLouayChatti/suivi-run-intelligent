import { SectionCard } from "@/components/app/page"
import { Badge } from "@/components/ui/badge"
import type { ApplicationHealth, HealthLevel } from "@/features/analytics/types"

const healthLabels: Record<HealthLevel, string> = {
  good: "Sain",
  warning: "À surveiller",
  critical: "Critique",
}

const healthVariants: Record<HealthLevel, "success" | "warning" | "destructive"> = {
  good: "success",
  warning: "warning",
  critical: "destructive",
}

interface ApplicationHealthCardsProps {
  data: ApplicationHealth[]
}

function ApplicationHealthCards({ data }: ApplicationHealthCardsProps) {
  return (
    <SectionCard title="Santé des applications" description="Vue d'ensemble par application">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {data.map((app) => (
          <div key={app.application} className="rounded-lg border border-border bg-background p-4">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold">{app.application}</p>
              <Badge variant={healthVariants[app.health]}>{healthLabels[app.health]}</Badge>
            </div>
            <dl className="mt-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Tickets actifs</dt>
                <dd className="font-medium tabular-nums">{app.activeTickets}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Résolution moyenne</dt>
                <dd className="font-medium tabular-nums">{app.avgResolutionHours.toFixed(1)} h</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Tickets urgents</dt>
                <dd className="font-medium tabular-nums">{app.urgentTickets}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </SectionCard>
  )
}

export { ApplicationHealthCards }
