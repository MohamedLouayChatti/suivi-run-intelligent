import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { EngineerDatum } from "@/features/analytics/types"

interface TransferRateChartProps {
  data: EngineerDatum[]
}

function TransferRateChart({ data }: TransferRateChartProps) {
  const chartData = data.map((d) => ({ label: d.engineer, value: d.value }))

  return (
    <SectionCard title="Taux de transfert par ingénieur" description="Part des tickets transférés">
      <HorizontalBarChart
        data={chartData}
        seriesName="Taux"
        labelWidth={130}
        valueFormatter={(v) => `${v.toFixed(1)} %`}
      />
    </SectionCard>
  )
}

export { TransferRateChart }
