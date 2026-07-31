import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { EngineerDatum } from "@/features/analytics/types"

interface AvgResolutionChartProps {
  data: EngineerDatum[]
}

function AvgResolutionChart({ data }: AvgResolutionChartProps) {
  const chartData = data.map((d) => ({ label: d.engineer, value: d.value }))

  return (
    <SectionCard title="Temps de résolution moyen par ingénieur" description="En heures">
      <HorizontalBarChart
        data={chartData}
        seriesName="Heures"
        labelWidth={130}
        valueFormatter={(v) => `${v.toFixed(1)} h`}
      />
    </SectionCard>
  )
}

export { AvgResolutionChart }
