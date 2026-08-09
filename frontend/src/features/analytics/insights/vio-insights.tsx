import { SectionCard } from "@/components/app/page"
import { StackedHorizontalBarChart } from "@/features/analytics/charts/stacked-horizontal-bar-chart"
import type { VioAppRow } from "@/features/analytics/types"

interface VioInsightsProps {
  rows: VioAppRow[]
}

// Each bar stacks Open + Resolved; Total is a direct label past the bar (it's the sum,
// not a third segment).
function VioInsights({ rows }: VioInsightsProps) {
  const data = rows.map((row) => ({
    label: row.vio_app,
    open: row.open,
    resolved: row.resolved,
    total: row.total,
  }))

  return (
    <SectionCard
      title="Répartition par application VIO"
      description="Ouverts vs résolus par application"
      action={
        <span className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full" style={{ background: "var(--color-chart-1)" }} /> Ouverts
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full" style={{ background: "var(--color-chart-4)" }} /> Résolus
          </span>
        </span>
      }
    >
      <StackedHorizontalBarChart
        data={data}
        segments={[
          { key: "open", label: "Ouverts", color: "var(--color-chart-1)" },
          { key: "resolved", label: "Résolus", color: "var(--color-chart-4)" },
        ]}
        totalKey="total"
        labelWidth={80}
        height={200}
        valueFormatter={(v) => String(v)}
      />
    </SectionCard>
  )
}

export { VioInsights }
