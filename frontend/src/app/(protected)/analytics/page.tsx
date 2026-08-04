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
import {
  getActivityTrend,
  getAttentionRequired,
  getCategoryDistribution,
  getJiraMetrics,
  getKpiSnapshot,
  getPriorityDistribution,
  getStatusDistribution,
} from "@/features/analytics/mock-data"
import { PriorityDistributionChart } from "@/features/analytics/priority-distribution-chart"
import { StatusDistributionChart } from "@/features/analytics/status-distribution-chart"
import { TeamOverview } from "@/features/analytics/team/team-overview"
import { usePermissions } from "@/lib/auth"
import { getAccessibleApplications, getPrimaryApplication } from "@/services/api/auth"

export default function AnalyticsPage() {
  const { user: currentUser, isAdmin } = usePermissions()
  const accessibleApplications = currentUser ? getAccessibleApplications(currentUser) : []
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null

  const [filters, setFilters] = useState<AnalyticsFilters>(defaultAnalyticsFilters)

  // Non-admins can never filter across every application, so their view defaults to (and never
  // offers "all", only) their own assignments — admins keep the "all applications" default.
  // Applied once so it never overrides a filter the user has since changed.
  const appliedDefaultRef = useRef(false)
  useEffect(() => {
    if (appliedDefaultRef.current || !currentUser) return
    if (!isAdmin && primaryApplication) {
      setFilters((prev) => ({ ...prev, application: primaryApplication }))
    }
    appliedDefaultRef.current = true
  }, [currentUser, isAdmin, primaryApplication])

  function handleFilterChange(patch: Partial<AnalyticsFilters>) {
    setFilters((prev) => ({ ...prev, ...patch }))
  }

  const snapshot = getKpiSnapshot(filters)
  const activity = getActivityTrend(filters)
  const statusDistribution = getStatusDistribution(filters)
  const categoryDistribution = getCategoryDistribution(filters)
  const priorityDistribution = getPriorityDistribution(filters)
  const jiraMetrics = getJiraMetrics(filters)
  const attention = getAttentionRequired(filters)

  // FCI has no additional widgets — Application Insights renders nothing for it.
  const showApplicationInsights = filters.application !== "all" && filters.application !== "FCI"
  const showAdminSections = filters.application === "all"

  return (
    <>
      <PageHeader
        title="Analyses"
        description="Performance opérationnelle du support — tickets, résolution, tendances"
        actions={
          <AnalyticsFilterControls
            filters={filters}
            onChange={handleFilterChange}
            isAdmin={isAdmin}
            accessibleApplications={accessibleApplications}
          />
        }
      />
      <PageBody className="space-y-6">
        <KpiSnapshotCards snapshot={snapshot} />

        <ActivityChart data={activity} />

        <div className="grid gap-6 xl:grid-cols-2">
          <StatusDistributionChart distribution={statusDistribution} />
          <CategoryDistributionChart distribution={categoryDistribution} />
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <PriorityDistributionChart distribution={priorityDistribution} />
          <JiraMetricsCard metrics={jiraMetrics} />
        </div>

        <AttentionRequiredSection data={attention} />

        {showApplicationInsights && <ApplicationInsights filters={filters} />}

        {showAdminSections && (
          <>
            <CrossApplicationOverview timeRange={filters.timeRange} />
            <TeamOverview timeRange={filters.timeRange} />
          </>
        )}
      </PageBody>
    </>
  )
}
