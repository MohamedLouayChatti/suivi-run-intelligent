import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import { categoryOptions } from "@/features/tickets/constants"
import type { components } from "@/types/api"

interface CategoryDistributionChartProps {
  distribution: components["schemas"]["DistributionsResponse"]["by_category"]
}

// Shared across every application — ranked magnitude, single hue (see HorizontalBarChart).
function CategoryDistributionChart({ distribution }: CategoryDistributionChartProps) {
  const data = categoryOptions
    .map((category) => ({ label: category, value: distribution[category] }))
    .sort((a, b) => b.value - a.value)

  return (
    <SectionCard title="Répartition par catégorie" description="Toutes applications confondues">
      <HorizontalBarChart data={data} seriesName="Tickets" labelWidth={168} />
    </SectionCard>
  )
}

export { CategoryDistributionChart }
