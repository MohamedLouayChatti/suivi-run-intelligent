"use client"

import { useQuery } from "@tanstack/react-query"

import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"
import {
  getActivityTrend,
  getAdminOverview,
  getApplicationInsights,
  getAttentionRequired,
  getDistributions,
  getJiraMetrics,
  getKpiSnapshot,
} from "@/services/api/analytics"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]
type TimeRange = components["schemas"]["TimeRange"]

function useKpiSnapshot(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: ["analytics", "kpi-snapshot", filters.application, filters.timeRange],
    queryFn: () => getKpiSnapshot(filters),
  })
}

function useActivityTrend(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: ["analytics", "activity-trend", filters.application, filters.timeRange],
    queryFn: () => getActivityTrend(filters),
  })
}

function useDistributions(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: ["analytics", "distributions", filters.application, filters.timeRange],
    queryFn: () => getDistributions(filters),
  })
}

function useJiraMetrics(filters: AnalyticsFilters) {
  return useQuery({
    queryKey: ["analytics", "jira-metrics", filters.application, filters.timeRange],
    queryFn: () => getJiraMetrics(filters),
  })
}

function useAttentionRequired(application: AnalyticsFilters["application"]) {
  return useQuery({
    queryKey: ["analytics", "attention-required", application],
    queryFn: () => getAttentionRequired({ application }),
  })
}

/** `application` may be null to skip the request entirely — e.g. while FCI or "all" is
 * selected, which have no dedicated insights widget (the backend 400s on FCI). */
function useApplicationInsights(application: Application | null, timeRange: TimeRange) {
  return useQuery({
    queryKey: ["analytics", "application-insights", application, timeRange],
    queryFn: () => getApplicationInsights(application as Application, timeRange),
    enabled: application !== null,
  })
}

/** Backs both CrossApplicationOverview and TeamOverview — same endpoint, same query
 * key, so TanStack Query dedupes the two mounts into a single request. */
function useAdminOverview(timeRange: TimeRange) {
  return useQuery({
    queryKey: ["analytics", "admin-overview", timeRange],
    queryFn: () => getAdminOverview(timeRange),
  })
}

export {
  useKpiSnapshot,
  useActivityTrend,
  useDistributions,
  useJiraMetrics,
  useAttentionRequired,
  useApplicationInsights,
  useAdminOverview,
}
