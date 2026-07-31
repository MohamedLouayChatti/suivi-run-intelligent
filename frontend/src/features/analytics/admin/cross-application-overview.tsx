import { ApplicationHealthCards } from "@/features/analytics/admin/application-health"
import { JiraDependency } from "@/features/analytics/admin/jira-dependency"
import { MonthlyTrends } from "@/features/analytics/admin/monthly-trends"
import { ResolutionTimeComparison } from "@/features/analytics/admin/resolution-time-comparison"
import { TransferRate } from "@/features/analytics/admin/transfer-rate"
import { WorkloadComparison } from "@/features/analytics/admin/workload-comparison"
import type { TimeRange } from "@/features/analytics/constants"
import {
  getApplicationHealth,
  getJiraDependency,
  getMonthlyTrends,
  getResolutionTimeComparison,
  getTransferRate,
  getWorkloadComparison,
} from "@/features/analytics/mock-data-admin"

interface CrossApplicationOverviewProps {
  timeRange: TimeRange
}

// Administrator-oriented — only rendered when "All Applications" is selected.
function CrossApplicationOverview({ timeRange }: CrossApplicationOverviewProps) {
  return (
    <div className="space-y-6">
      <WorkloadComparison rows={getWorkloadComparison(timeRange)} />
      <ApplicationHealthCards data={getApplicationHealth(timeRange)} />
      <div className="grid gap-6 xl:grid-cols-2">
        <ResolutionTimeComparison data={getResolutionTimeComparison(timeRange)} />
        <JiraDependency data={getJiraDependency(timeRange)} />
      </div>
      <TransferRate data={getTransferRate(timeRange)} />
      <MonthlyTrends data={getMonthlyTrends(timeRange)} />
    </div>
  )
}

export { CrossApplicationOverview }
