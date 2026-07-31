import { SectionCard } from "@/components/app/page"
import { VerticalBarChart } from "@/features/analytics/charts/vertical-bar-chart"
import type { EngineerDatum } from "@/features/analytics/types"

interface ResolvedTicketsChartProps {
  data: EngineerDatum[]
}

function ResolvedTicketsChart({ data }: ResolvedTicketsChartProps) {
  const chartData = data.map((d) => ({ label: d.engineer.split(" ")[0], value: d.value }))

  return (
    <SectionCard title="Tickets résolus par ingénieur" description="Volume résolu sur la période">
      <VerticalBarChart data={chartData} seriesName="Tickets résolus" />
    </SectionCard>
  )
}

export { ResolvedTicketsChart }
