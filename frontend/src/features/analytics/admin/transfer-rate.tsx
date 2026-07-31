import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

interface TransferRateProps {
  data: { application: Application; transferRatePct: number }[]
}

function TransferRate({ data }: TransferRateProps) {
  const chartData = data.map((d) => ({ label: d.application, value: d.transferRatePct }))

  return (
    <SectionCard title="Taux de transfert" description="Part des tickets transférés par application">
      <HorizontalBarChart
        data={chartData}
        seriesName="Taux"
        labelWidth={90}
        height={200}
        valueFormatter={(v) => `${v.toFixed(1)} %`}
      />
    </SectionCard>
  )
}

export { TransferRate }
