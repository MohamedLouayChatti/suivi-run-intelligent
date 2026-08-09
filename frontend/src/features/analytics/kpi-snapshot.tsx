import { Activity, AlertTriangle, CheckCircle2, Clock3, TrendingDown, TrendingUp, Ticket } from "lucide-react"
import type { LucideIcon } from "lucide-react"

import type { KpiSnapshot } from "@/features/analytics/types"

function formatDuration(hours: number): string {
  if (hours < 1) return `${Math.round(hours * 60)} min`
  const wholeHours = Math.floor(hours)
  const minutes = Math.round((hours - wholeHours) * 60)
  return minutes === 0 ? `${wholeHours} h` : `${wholeHours} h ${minutes} min`
}

function formatTrend(changePct: number): string {
  const sign = changePct > 0 ? "+" : ""
  return `${sign}${changePct.toFixed(1)}%`
}

interface KpiSnapshotCardsProps {
  snapshot: KpiSnapshot
}

// Operational Snapshot — five KPI tiles, same tile markup as the Dashboard's
// KpiCards, extended with a trend delta vs the previous period. Kept neutral (no
// green/red judgment) in line with the app's single-hue design language.
function KpiSnapshotCards({ snapshot }: KpiSnapshotCardsProps) {
  const kpis: { label: string; value: string; icon: LucideIcon; changePct: number }[] = [
    {
      label: "Total tickets",
      value: String(snapshot.total_tickets),
      icon: Ticket,
      changePct: snapshot.trends.total_tickets,
    },
    {
      label: "Tickets ouverts",
      value: String(snapshot.open_tickets),
      icon: Activity,
      changePct: snapshot.trends.open_tickets,
    },
    {
      label: "Tickets résolus",
      value: String(snapshot.resolved_tickets),
      icon: CheckCircle2,
      changePct: snapshot.trends.resolved_tickets,
    },
    {
      label: "Temps de résolution moyen",
      value: formatDuration(snapshot.avg_resolution_hours),
      icon: Clock3,
      changePct: snapshot.trends.avg_resolution_hours,
    },
    {
      label: "Tickets urgents",
      value: String(snapshot.urgent_tickets),
      icon: AlertTriangle,
      changePct: snapshot.trends.urgent_tickets,
    },
  ]

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      {kpis.map((k) => {
        const TrendIcon = k.changePct >= 0 ? TrendingUp : TrendingDown
        return (
          <div key={k.label} className="rounded-lg border border-border bg-card p-5">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {k.label}
              </p>
              <k.icon className="size-4 text-muted-foreground" strokeWidth={1.75} />
            </div>
            <p className="mt-3 text-3xl font-semibold tabular-nums">{k.value}</p>
            <div className="mt-2 flex items-center gap-1.5 text-xs">
              <TrendIcon className="size-3.5 text-muted-foreground" strokeWidth={2} />
              <span className="font-medium tabular-nums">{formatTrend(k.changePct)}</span>
              <span className="text-muted-foreground">vs période précédente</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export { KpiSnapshotCards }
