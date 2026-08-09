import { ApplicationHealthCards } from "@/features/analytics/admin/application-health"
import { JiraDependency } from "@/features/analytics/admin/jira-dependency"
import { MonthlyTrends } from "@/features/analytics/admin/monthly-trends"
import { ResolutionTimeComparison } from "@/features/analytics/admin/resolution-time-comparison"
import { TransferRate } from "@/features/analytics/admin/transfer-rate"
import { WorkloadComparison } from "@/features/analytics/admin/workload-comparison"
import type { TimeRange } from "@/features/analytics/constants"
import { useAdminOverview } from "@/features/analytics/use-analytics"

interface CrossApplicationOverviewProps {
  timeRange: TimeRange
}

// Administrator-oriented — only rendered when "All Applications" is selected.
function CrossApplicationOverview({ timeRange }: CrossApplicationOverviewProps) {
  const { data } = useAdminOverview(timeRange)
  if (!data) return null

  return (
    <div className="space-y-6">
      <WorkloadComparison rows={data.workload} />
      <ApplicationHealthCards data={data.health} />
      <div className="grid gap-6 xl:grid-cols-2">
        <ResolutionTimeComparison data={data.resolution_time} />
        <JiraDependency data={data.jira_dependency} />
      </div>
      <TransferRate data={data.transfer_rate} />
      <MonthlyTrends data={data.monthly_trends} />
    </div>
  )
}

export { CrossApplicationOverview }
