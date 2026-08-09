import type { components } from "@/types/api"

import { httpClient } from "./client"

type Application = components["schemas"]["Application"]
type TimeRange = components["schemas"]["TimeRange"]
type KpiSnapshotResponse = components["schemas"]["KpiSnapshotResponse"]
type ActivityPointResponse = components["schemas"]["ActivityPointResponse"]
type DistributionsResponse = components["schemas"]["DistributionsResponse"]
type JiraMetricsResponse = components["schemas"]["JiraMetricsResponse"]
type AttentionRequiredResponse = components["schemas"]["AttentionRequiredResponse"]
type ApplicationInsightsResponse = components["schemas"]["ApplicationInsightsResponse"]
type AdminOverviewResponse = components["schemas"]["AdminOverviewResponse"]
type MyKpiSnapshotResponse = components["schemas"]["MyKpiSnapshotResponse"]

interface AnalyticsScopeParams {
  application?: Application | "all"
  timeRange: TimeRange
}

function applicationParam(application: Application | "all" | undefined): Application | undefined {
  return application === "all" ? undefined : application
}

async function getKpiSnapshot(params: AnalyticsScopeParams): Promise<KpiSnapshotResponse> {
  const { data } = await httpClient.get<KpiSnapshotResponse>("/analytics/kpi-snapshot", {
    params: { application: applicationParam(params.application), time_range: params.timeRange },
  })
  return data
}

async function getActivityTrend(params: AnalyticsScopeParams): Promise<ActivityPointResponse[]> {
  const { data } = await httpClient.get<ActivityPointResponse[]>("/analytics/activity-trend", {
    params: { application: applicationParam(params.application), time_range: params.timeRange },
  })
  return data
}

async function getDistributions(params: AnalyticsScopeParams): Promise<DistributionsResponse> {
  const { data } = await httpClient.get<DistributionsResponse>("/analytics/distributions", {
    params: { application: applicationParam(params.application), time_range: params.timeRange },
  })
  return data
}

async function getJiraMetrics(params: AnalyticsScopeParams): Promise<JiraMetricsResponse> {
  const { data } = await httpClient.get<JiraMetricsResponse>("/analytics/jira-metrics", {
    params: { application: applicationParam(params.application), time_range: params.timeRange },
  })
  return data
}

async function getAttentionRequired(
  params: Pick<AnalyticsScopeParams, "application"> & { thresholdDays?: number }
): Promise<AttentionRequiredResponse> {
  const { data } = await httpClient.get<AttentionRequiredResponse>("/analytics/attention-required", {
    params: { application: applicationParam(params.application), threshold_days: params.thresholdDays },
  })
  return data
}

async function getApplicationInsights(
  application: Application,
  timeRange: TimeRange
): Promise<ApplicationInsightsResponse> {
  const { data } = await httpClient.get<ApplicationInsightsResponse>("/analytics/application-insights", {
    params: { application, time_range: timeRange },
  })
  return data
}

async function getAdminOverview(timeRange: TimeRange): Promise<AdminOverviewResponse> {
  const { data } = await httpClient.get<AdminOverviewResponse>("/analytics/admin-overview", {
    params: { time_range: timeRange },
  })
  return data
}

async function getMyKpiSnapshot(): Promise<MyKpiSnapshotResponse> {
  const { data } = await httpClient.get<MyKpiSnapshotResponse>("/analytics/my-kpi-snapshot")
  return data
}

async function getMyActivityTrend(): Promise<ActivityPointResponse[]> {
  const { data } = await httpClient.get<ActivityPointResponse[]>("/analytics/my-activity-trend")
  return data
}

export {
  getKpiSnapshot,
  getActivityTrend,
  getDistributions,
  getJiraMetrics,
  getAttentionRequired,
  getApplicationInsights,
  getAdminOverview,
  getMyKpiSnapshot,
  getMyActivityTrend,
}
export type {
  KpiSnapshotResponse,
  ActivityPointResponse,
  DistributionsResponse,
  JiraMetricsResponse,
  AttentionRequiredResponse,
  ApplicationInsightsResponse,
  AdminOverviewResponse,
  MyKpiSnapshotResponse,
}
