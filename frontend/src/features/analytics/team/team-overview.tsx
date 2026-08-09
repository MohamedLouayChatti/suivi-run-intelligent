import type { TimeRange } from "@/features/analytics/constants"
import { useAdminOverview } from "@/features/analytics/use-analytics"
import { ActiveTicketsChart } from "@/features/analytics/team/active-tickets-chart"
import { AssignmentDistributionChart } from "@/features/analytics/team/assignment-distribution-chart"
import { AvgResolutionChart } from "@/features/analytics/team/avg-resolution-chart"
import { ResolvedTicketsChart } from "@/features/analytics/team/resolved-tickets-chart"
import { TransferRateChart } from "@/features/analytics/team/transfer-rate-chart"

interface TeamOverviewProps {
  timeRange: TimeRange
}

// "All Applications" only — lets supervisors read workload distribution as operational
// insight, not as a ranking, hence the neutral chart titles throughout. Shares its
// query (and cache) with CrossApplicationOverview — same admin-overview endpoint.
function TeamOverview({ timeRange }: TeamOverviewProps) {
  const { data } = useAdminOverview(timeRange)
  if (!data) return null

  const { team } = data

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Vue d&apos;ensemble de l&apos;équipe</h2>
        <p className="text-sm text-muted-foreground">
          Répartition de la charge de travail entre ingénieurs
        </p>
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <ActiveTicketsChart data={team.active_tickets} />
        <AssignmentDistributionChart data={team.assignment_distribution} />
      </div>
      <ResolvedTicketsChart data={team.resolved_tickets} />
      <div className="grid gap-6 xl:grid-cols-2">
        <AvgResolutionChart data={team.avg_resolution_hours} />
        <TransferRateChart data={team.transfer_rate_pct} />
      </div>
    </div>
  )
}

export { TeamOverview }
