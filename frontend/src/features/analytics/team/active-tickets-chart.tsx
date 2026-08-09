import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { EngineerDatum } from "@/features/analytics/types"

interface ActiveTicketsChartProps {
  data: EngineerDatum[]
}

function ActiveTicketsChart({ data }: ActiveTicketsChartProps) {
  const chartData = data.map((d) => ({ label: d.engineer?.display_name ?? "Utilisateur inconnu", value: d.value }))

  return (
    <SectionCard title="Tickets actifs par ingénieur" description="Charge de travail en cours">
      <HorizontalBarChart data={chartData} seriesName="Tickets actifs" labelWidth={130} />
    </SectionCard>
  )
}

export { ActiveTicketsChart }
