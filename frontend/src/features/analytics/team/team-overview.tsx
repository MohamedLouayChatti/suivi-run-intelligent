import type { TimeRange } from "@/features/analytics/constants"
import {
  getActiveTicketsPerEngineer,
  getAssignmentDistribution,
  getAvgResolutionPerEngineer,
  getResolvedTicketsPerEngineer,
  getTransferRatePerEngineer,
} from "@/features/analytics/mock-data-admin"
import { ActiveTicketsChart } from "@/features/analytics/team/active-tickets-chart"
import { AssignmentDistributionChart } from "@/features/analytics/team/assignment-distribution-chart"
import { AvgResolutionChart } from "@/features/analytics/team/avg-resolution-chart"
import { ResolvedTicketsChart } from "@/features/analytics/team/resolved-tickets-chart"
import { TransferRateChart } from "@/features/analytics/team/transfer-rate-chart"

interface TeamOverviewProps {
  timeRange: TimeRange
}

// "All Applications" only — lets supervisors read workload distribution as operational
// insight, not as a ranking, hence the neutral chart titles throughout.
function TeamOverview({ timeRange }: TeamOverviewProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Vue d&apos;ensemble de l&apos;équipe</h2>
        <p className="text-sm text-muted-foreground">
          Répartition de la charge de travail entre ingénieurs
        </p>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <ActiveTicketsChart data={getActiveTicketsPerEngineer(timeRange)} />
        <AssignmentDistributionChart data={getAssignmentDistribution(timeRange)} />
      </div>
      <ResolvedTicketsChart data={getResolvedTicketsPerEngineer(timeRange)} />
      <div className="grid gap-6 xl:grid-cols-2">
        <AvgResolutionChart data={getAvgResolutionPerEngineer(timeRange)} />
        <TransferRateChart data={getTransferRatePerEngineer(timeRange)} />
      </div>
    </div>
  )
}

export { TeamOverview }
