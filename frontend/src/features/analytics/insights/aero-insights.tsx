import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { RankedEntry } from "@/features/analytics/types"

interface AeroInsightsProps {
  topElements: RankedEntry[]
}

// "Top catégories" was dropped — it duplicated the shared Category Distribution chart
// above (§3). Top Elements takes the full width freed up by its removal.
function AeroInsights({ topElements }: AeroInsightsProps) {
  const elementData = topElements.map((e) => ({ label: e.label, value: e.count }))

  return (
    <SectionCard title="Top éléments" description="Éléments les plus fréquemment concernés">
      <HorizontalBarChart data={elementData} seriesName="Tickets" labelWidth={220} height={288} />
    </SectionCard>
  )
}

export { AeroInsights }
