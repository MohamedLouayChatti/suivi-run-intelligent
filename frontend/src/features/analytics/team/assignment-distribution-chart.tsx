import { SectionCard } from "@/components/app/page"
import { DonutChart } from "@/features/analytics/charts/donut-chart"
import type { EngineerDatum } from "@/features/analytics/types"

interface AssignmentDistributionChartProps {
  data: EngineerDatum[]
}

// No dedicated 6-way categorical palette exists in the design system, so identity is
// expressed the same way status/priority already do: one hue, stepped opacity.
function AssignmentDistributionChart({ data }: AssignmentDistributionChartProps) {
  const total = data.reduce((sum, d) => sum + d.value, 0)
  const chartData = data.map((d, index) => ({
    label: d.engineer?.display_name ?? "Utilisateur inconnu",
    value: d.value,
    color: `color-mix(in oklch, var(--color-primary) ${Math.max(15, 42 - index * 6)}%, var(--color-muted))`,
  }))

  return (
    <SectionCard title="Répartition des affectations" description="Répartition de la propriété des tickets">
      <DonutChart
        data={chartData}
        centerLabel={
          <div className="text-center">
            <p className="text-2xl font-semibold tabular-nums">{total}</p>
            <p className="text-xs text-muted-foreground">tickets</p>
          </div>
        }
      />
    </SectionCard>
  )
}

export { AssignmentDistributionChart }
