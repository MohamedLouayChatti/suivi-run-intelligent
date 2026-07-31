import { SectionCard } from "@/components/app/page"
import { statusConfig } from "@/components/app/status"
import { DonutChart } from "@/features/analytics/charts/donut-chart"
import type { components } from "@/types/api"

type Status = components["schemas"]["Status"]

// Fixed categorical order — mirrors the Dashboard's ticket-status-summary ordering —
// mapped onto the app's dedicated --chart-1..5 tokens (an orange-to-neutral ramp sized
// exactly for 5 series).
const statusOrder: Status[] = ["OPEN", "IN_PROGRESS", "RESOLVED", "TRANSFERRED", "CLOSED"]
const statusChartColor: Record<Status, string> = {
  OPEN: "var(--color-chart-1)",
  IN_PROGRESS: "var(--color-chart-2)",
  RESOLVED: "var(--color-chart-3)",
  TRANSFERRED: "var(--color-chart-4)",
  CLOSED: "var(--color-chart-5)",
}

interface StatusDistributionChartProps {
  distribution: Record<Status, number>
}

function StatusDistributionChart({ distribution }: StatusDistributionChartProps) {
  const total = statusOrder.reduce((sum, status) => sum + distribution[status], 0)
  const data = statusOrder.map((status) => ({
    label: statusConfig[status].label,
    value: distribution[status],
    color: statusChartColor[status],
  }))

  return (
    <SectionCard title="Répartition par statut" description="Tous statuts confondus">
      <DonutChart data={data} centerLabel={<CenterTotal total={total} />} />
    </SectionCard>
  )
}

function CenterTotal({ total }: { total: number }) {
  return (
    <div className="text-center">
      <p className="text-2xl font-semibold tabular-nums">{total}</p>
      <p className="text-xs text-muted-foreground">tickets</p>
    </div>
  )
}

export { StatusDistributionChart }
