import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { AppResolutionTime } from "@/features/analytics/types"

interface ResolutionTimeComparisonProps {
  data: AppResolutionTime[]
}

function ResolutionTimeComparison({ data }: ResolutionTimeComparisonProps) {
  const chartData = data.map((d) => ({ label: d.application, value: d.avg_resolution_hours }))

  return (
    <SectionCard
      title="Comparaison des temps de résolution"
      description="Temps de résolution moyen par application"
    >
      <HorizontalBarChart
        data={chartData}
        seriesName="Heures"
        labelWidth={90}
        height={200}
        valueFormatter={(v) => `${v.toFixed(1)} h`}
      />
    </SectionCard>
  )
}

export { ResolutionTimeComparison }
