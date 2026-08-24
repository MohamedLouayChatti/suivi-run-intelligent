"use client"

import { useEffect, useRef, useState } from "react"

import { PageBody, PageHeader } from "@/components/app/page"
import { AnalyticsFilterControls } from "@/features/analytics/analytics-filters"
import { CrossApplicationOverview } from "@/features/analytics/admin/cross-application-overview"
import { AttentionRequiredSection } from "@/features/analytics/attention-required"
import { ActivityChart } from "@/features/analytics/activity-chart"
import { CategoryDistributionChart } from "@/features/analytics/category-distribution-chart"
import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"
import { defaultAnalyticsFilters } from "@/features/analytics/filter-analytics"
import { ApplicationInsights } from "@/features/analytics/insights/application-insights"
import { JiraMetricsCard } from "@/features/analytics/jira-metrics"
import { KpiSnapshotCards } from "@/features/analytics/kpi-snapshot"
import { PriorityDistributionChart } from "@/features/analytics/priority-distribution-chart"
import { StatusDistributionChart } from "@/features/analytics/status-distribution-chart"
import { TeamOverview } from "@/features/analytics/team/team-overview"
import {
  useActivityTrend,
  useAttentionRequired,
  useDistributions,
  useJiraMetrics,
  useKpiSnapshot,
} from "@/features/analytics/use-analytics"
import { RequireRouteAccess, usePermissions } from "@/lib/auth"
import { getAccessibleApplications, getPrimaryApplication } from "@/services/api/auth"

export default function AnalyticsPage() {
  const { user: currentUser, hasPermission } = usePermissions()
  // Mirrors the backend's analytics application scope: holding the breadth permission is what
  // lets a caller span every application, rather than belonging to any particular role.
  const canReadAllApplications = hasPermission("analytics.read_any_application")
  const accessibleApplications = currentUser ? getAccessibleApplications(currentUser) : []
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null

  const [filters, setFilters] = useState<AnalyticsFilters>(defaultAnalyticsFilters)

  // Without the breadth permission a user can never filter across every application, so their
  // view defaults to (and only ever offers) their own assignments — holders keep "all".
  // Applied once so it never overrides a filter the user has since changed.
  const appliedDefaultRef = useRef(false)
  useEffect(() => {
    if (appliedDefaultRef.current || !currentUser) return
    if (!canReadAllApplications && primaryApplication) {
      setFilters((prev) => ({ ...prev, application: primaryApplication }))
    }
    appliedDefaultRef.current = true
  }, [currentUser, canReadAllApplications, primaryApplication])

  function handleFilterChange(patch: Partial<AnalyticsFilters>) {
    setFilters((prev) => ({ ...prev, ...patch }))
  }

  const { data: snapshot } = useKpiSnapshot(filters)
  const { data: activity } = useActivityTrend(filters)
  const { data: distributions } = useDistributions(filters)
  const { data: jiraMetrics } = useJiraMetrics(filters)
  const { data: attention } = useAttentionRequired(filters.application)

  // FCI has no additional widgets — Application Insights renders nothing for it.
  const showApplicationInsights = filters.application !== "all" && filters.application !== "FCI"
  // Both the breadth permission and the cross-application view: `/analytics/admin-overview` is
  // gated on `analytics.read_any_application` alone, and a caller without it whose account has
  // no primary application keeps the "all" default, which used to render these into a 403.
  const showAdminSections = canReadAllApplications && filters.application === "all"

  return (
    <RequireRouteAccess href="/analytics">
      <PageHeader
        title="Analyses"
        description="Performance opérationnelle du support — tickets, résolution, tendances"
        actions={
          <AnalyticsFilterControls
            filters={filters}
            onChange={handleFilterChange}
            canReadAllApplications={canReadAllApplications}
            accessibleApplications={accessibleApplications}
          />
        }
      />
      <PageBody className="space-y-6">
        {snapshot && <KpiSnapshotCards snapshot={snapshot} />}

        {activity && <ActivityChart data={activity} timeRange={filters.timeRange} />}

        <div className="grid gap-6 xl:grid-cols-2">
          {distributions && <StatusDistributionChart distribution={distributions.by_status} />}
          {distributions && <CategoryDistributionChart distribution={distributions.by_category} />}
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          {distributions && <PriorityDistributionChart distribution={distributions.by_priority} />}
          {jiraMetrics && <JiraMetricsCard metrics={jiraMetrics} />}
        </div>

        {attention && <AttentionRequiredSection data={attention} />}

        {showApplicationInsights && <ApplicationInsights filters={filters} />}

        {showAdminSections && (
          <>
            <CrossApplicationOverview timeRange={filters.timeRange} />
            <TeamOverview timeRange={filters.timeRange} />
          </>
        )}
      </PageBody>
    </RequireRouteAccess>
  )
}
