import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { AppJiraDependency } from "@/features/analytics/types"

interface JiraDependencyProps {
  data: AppJiraDependency[]
}

function JiraDependency({ data }: JiraDependencyProps) {
  const chartData = data.map((d) => ({ label: d.application, value: d.jira_incidents }))

  return (
    <SectionCard title="Dépendance à Jira" description="Incidents liés à Jira par application">
      <HorizontalBarChart data={chartData} seriesName="Incidents" labelWidth={90} height={200} />
    </SectionCard>
  )
}

export { JiraDependency }
