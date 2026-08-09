import type { components } from "@/types/api"

// Thin aliases onto the backend's generated response shapes — kept here so widget
// components don't each spell out `components["schemas"][...]`, same convention as
// services/api/*.ts. Fields stay snake_case, matching every other feature module.
type KpiSnapshot = components["schemas"]["KpiSnapshotResponse"]
type ActivityPoint = components["schemas"]["ActivityPointResponse"]
type JiraMetrics = components["schemas"]["JiraMetricsResponse"]
type AgingIncident = components["schemas"]["AgingIncidentResponse"]
type AttentionRequired = components["schemas"]["AttentionRequiredResponse"]
type HealthLevel = components["schemas"]["HealthLevel"]
type ApplicationHealth = components["schemas"]["ApplicationHealthResponse"]
type ColorisHeatmapCell = components["schemas"]["ColorisHeatmapCellResponse"]
type RankedEntry = components["schemas"]["RankedEntryResponse"]
type VioAppRow = components["schemas"]["VioAppRowResponse"]
type AppWorkloadRow = components["schemas"]["AppWorkloadRowResponse"]
type AppResolutionTime = components["schemas"]["AppResolutionTimeResponse"]
type AppJiraDependency = components["schemas"]["AppJiraDependencyResponse"]
type AppTransferRate = components["schemas"]["AppTransferRateResponse"]
type AppMonthlyTrendPoint = components["schemas"]["AppMonthlyTrendPointResponse"]
type EngineerDatum = components["schemas"]["EngineerDatumResponse"]
type AdminOverview = components["schemas"]["AdminOverviewResponse"]

export type {
  KpiSnapshot,
  ActivityPoint,
  JiraMetrics,
  AgingIncident,
  AttentionRequired,
  HealthLevel,
  ApplicationHealth,
  ColorisHeatmapCell,
  RankedEntry,
  VioAppRow,
  AppWorkloadRow,
  AppResolutionTime,
  AppJiraDependency,
  AppTransferRate,
  AppMonthlyTrendPoint,
  EngineerDatum,
  AdminOverview,
}
