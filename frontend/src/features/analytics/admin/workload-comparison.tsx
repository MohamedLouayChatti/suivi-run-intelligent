import { SectionCard } from "@/components/app/page"
import { StackedHorizontalBarChart } from "@/features/analytics/charts/stacked-horizontal-bar-chart"
import type { AppWorkloadRow } from "@/features/analytics/types"

interface WorkloadComparisonProps {
  rows: AppWorkloadRow[]
}

function WorkloadComparison({ rows }: WorkloadComparisonProps) {
  const data = rows.map((row) => ({
    label: row.application,
    open: row.open,
    inProgress: row.inProgress,
    resolved: row.resolved,
  }))

  return (
    <SectionCard
      title="Comparaison de la charge entre applications"
      description="Tickets ouverts, en cours et résolus par application"
      action={
        <span className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full" style={{ background: "var(--color-chart-1)" }} /> Ouverts
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full" style={{ background: "var(--color-chart-2)" }} /> En cours
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
          { key: "inProgress", label: "En cours", color: "var(--color-chart-2)" },
          { key: "resolved", label: "Résolus", color: "var(--color-chart-4)" },
        ]}
        labelWidth={90}
        height={200}
      />
    </SectionCard>
  )
}

export { WorkloadComparison }
