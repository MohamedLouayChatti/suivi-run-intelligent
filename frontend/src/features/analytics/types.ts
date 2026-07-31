import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]
type Priority = components["schemas"]["Priority"]
type Offer = components["schemas"]["Offer"]
type Version = components["schemas"]["Version"]
type VioApp = components["schemas"]["VioApp"]

interface KpiSnapshot {
  totalTickets: number
  openTickets: number
  resolvedTickets: number
  avgResolutionHours: number
  urgentTickets: number
  trends: {
    totalTickets: number
    openTickets: number
    resolvedTickets: number
    avgResolutionHours: number
    urgentTickets: number
  }
}

interface ActivityPoint {
  date: string
  label: string
  created: number
  resolved: number
}

interface JiraMetrics {
  requiresJira: number
  transferredToJira: number
  awaitingDelivery: number
  avgDeliveryDelayDays: number
}

interface AgingIncident {
  ticketId: string
  title: string
  ageDays: number
  priority: Priority
  assignee: string
}

interface AttentionRequired {
  /** Total incidents older than thresholdDays — may exceed incidents.length. */
  count: number
  thresholdDays: number
  incidents: AgingIncident[]
}

type HealthLevel = "good" | "warning" | "critical"

interface ApplicationHealth {
  application: Application
  health: HealthLevel
  activeTickets: number
  avgResolutionHours: number
  urgentTickets: number
}

interface ColorisHeatmapCell {
  offer: Offer
  version: Version
  count: number
}

interface RankedEntry {
  label: string
  count: number
}

interface VioAppRow {
  vioApp: VioApp
  open: number
  resolved: number
  total: number
}

interface AppWorkloadRow {
  application: Application
  open: number
  inProgress: number
  resolved: number
}

interface AppMonthlyTrendPoint {
  month: string
  FCI: number
  COLORIS: number
  AERO: number
  VIO: number
}

interface EngineerDatum {
  engineer: string
  value: number
}

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
  AppMonthlyTrendPoint,
  EngineerDatum,
}
