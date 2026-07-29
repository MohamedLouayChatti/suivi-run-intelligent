import { Activity, CheckCircle2, Plus, Clock3 } from "lucide-react"
import type { LucideIcon } from "lucide-react"

function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60)
  const remaining = minutes % 60
  if (hours === 0) return `${remaining} min`
  if (remaining === 0) return `${hours} h`
  return `${hours} h ${remaining} min`
}

interface KpiCardsProps {
  activeAssignments: number
  resolvedThisWeek: number
  createdThisWeek: number
  avgResolutionMinutes: number
}

function KpiCards({
  activeAssignments,
  resolvedThisWeek,
  createdThisWeek,
  avgResolutionMinutes,
}: KpiCardsProps) {
  const kpis: { label: string; value: string; icon: LucideIcon }[] = [
    { label: "Affectations actives", value: String(activeAssignments), icon: Activity },
    { label: "Résolus cette semaine", value: String(resolvedThisWeek), icon: CheckCircle2 },
    { label: "Créés cette semaine", value: String(createdThisWeek), icon: Plus },
    { label: "Temps de résolution moyen", value: formatDuration(avgResolutionMinutes), icon: Clock3 },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {kpis.map((k) => (
        <div key={k.label} className="rounded-lg border border-border bg-card p-5">
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {k.label}
            </p>
            <k.icon className="size-4 text-muted-foreground" strokeWidth={1.75} />
          </div>
          <p className="mt-3 text-3xl font-semibold tabular-nums">{k.value}</p>
        </div>
      ))}
    </div>
  )
}

export { KpiCards }
