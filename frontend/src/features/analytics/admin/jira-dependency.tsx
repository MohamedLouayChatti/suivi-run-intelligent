import { SectionCard } from "@/components/app/page"
import { HorizontalBarChart } from "@/features/analytics/charts/horizontal-bar-chart"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

interface JiraDependencyProps {
  data: { application: Application; jiraIncidents: number }[]
}

function JiraDependency({ data }: JiraDependencyProps) {
  const chartData = data.map((d) => ({ label: d.application, value: d.jiraIncidents }))

  return (
    <SectionCard title="Dépendance à Jira" description="Incidents liés à Jira par application">
      <HorizontalBarChart data={chartData} seriesName="Incidents" labelWidth={90} height={200} />
    </SectionCard>
  )
}

export { JiraDependency }
