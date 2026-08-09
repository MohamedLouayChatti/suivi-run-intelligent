import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { AppTransferRate } from "@/features/analytics/types"

interface TransferRateProps {
  data: AppTransferRate[]
}

function TransferRate({ data }: TransferRateProps) {
  const chartData = data.map((d) => ({ label: d.application, value: d.transfer_rate_pct }))

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
