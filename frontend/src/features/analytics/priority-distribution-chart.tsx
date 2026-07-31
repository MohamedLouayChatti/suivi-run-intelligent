import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import { priorityOptions } from "@/features/tickets/constants"
import type { components } from "@/types/api"

type Priority = components["schemas"]["Priority"]

interface PriorityDistributionChartProps {
  distribution: Record<Priority, number>
}

// Kept in severity order (P1 → P4), not sorted by count — priority has an intrinsic
// ranking that should stay readable regardless of the data.
function PriorityDistributionChart({ distribution }: PriorityDistributionChartProps) {
  const data = priorityOptions.map((priority) => ({
    label: priority,
    value: distribution[priority],
  }))

  return (
    <SectionCard title="Répartition par priorité" description="P1 = priorité la plus haute">
      <HorizontalBarChart data={data} seriesName="Tickets" labelWidth={60} height={220} />
    </SectionCard>
  )
}

export { PriorityDistributionChart }
