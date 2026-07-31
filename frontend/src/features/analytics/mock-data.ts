import type { components } from "@/types/api"

import { timeRangeDays, type TimeRange } from "@/features/analytics/constants"
import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"
import { createSeededRandom, randomInt } from "@/features/analytics/random"
import type {
  ActivityPoint,
  AgingIncident,
  AttentionRequired,
  JiraMetrics,
  KpiSnapshot,
} from "@/features/analytics/types"
import { priorityOptions } from "@/features/tickets/constants"

type Application = components["schemas"]["Application"]
type Status = components["schemas"]["Status"]
type Category = components["schemas"]["Category"]
type Priority = components["schemas"]["Priority"]

// No /analytics endpoint exists yet — every getX(filters) below is mocked and
// deterministic per filter combination (same filters always render the same numbers),
// isolated here for a later one-file swap to a real services/api/analytics.ts call.

// Relative daily ticket volume per application — VIO carries the highest customer
// contact volume, AERO the lowest. "all" sums every application.
const applicationDailyWeight: Record<Application, number> = {
  FCI: 4.2,
  COLORIS: 3.1,
  AERO: 1.8,
  VIO: 5.4,
}

function totalDailyWeight(application: Application | "all"): number {
  if (application === "all") {
    return Object.values(applicationDailyWeight).reduce((sum, w) => sum + w, 0)
  }
  return applicationDailyWeight[application]
}

function seedFor(filters: AnalyticsFilters, section: string): string {
  return `${section}:${filters.application}:${filters.timeRange}`
}

function getKpiSnapshot(filters: AnalyticsFilters): KpiSnapshot {
  const rng = createSeededRandom(seedFor(filters, "kpi"))
  const days = timeRangeDays[filters.timeRange]
  const total = Math.round(totalDailyWeight(filters.application) * days * (0.9 + rng() * 0.2))
  const openShare = 0.16 + rng() * 0.05
  const resolvedShare = 0.62 + rng() * 0.08
  const urgentShare = 0.05 + rng() * 0.03

  const openTickets = Math.round(total * openShare)
  const resolvedTickets = Math.round(total * resolvedShare)
  const urgentTickets = Math.max(1, Math.round(total * urgentShare))
  const avgResolutionHours = Math.round((6 + rng() * 30) * 10) / 10

  const trend = () => Math.round((rng() - 0.45) * 240) / 10

  return {
    totalTickets: total,
    openTickets,
    resolvedTickets,
    avgResolutionHours,
    urgentTickets,
    trends: {
      totalTickets: trend(),
      openTickets: trend(),
      resolvedTickets: trend(),
      avgResolutionHours: trend(),
      urgentTickets: trend(),
    },
  }
}

function bucketCount(timeRange: TimeRange): number {
  const table: Record<TimeRange, number> = { "30D": 30, "3M": 13, "6M": 6, "1Y": 12 }
  return table[timeRange]
}

function bucketSpanDays(timeRange: TimeRange): number {
  const table: Record<TimeRange, number> = { "30D": 1, "3M": 7, "6M": 30, "1Y": 30 }
  return table[timeRange]
}

const dayFormatter = new Intl.DateTimeFormat("fr-FR", { day: "2-digit", month: "2-digit" })
const monthFormatter = new Intl.DateTimeFormat("fr-FR", { month: "short" })

function getActivityTrend(filters: AnalyticsFilters): ActivityPoint[] {
  const rng = createSeededRandom(seedFor(filters, "activity"))
  const count = bucketCount(filters.timeRange)
  const spanDays = bucketSpanDays(filters.timeRange)
  const dailyBase = totalDailyWeight(filters.application)
  const useDayLabel = filters.timeRange === "30D" || filters.timeRange === "3M"
  const points: ActivityPoint[] = []

  for (let i = count - 1; i >= 0; i--) {
    const date = new Date(Date.now() - i * spanDays * 24 * 60 * 60 * 1000)
    const seasonal = 1 + 0.25 * Math.sin(i / (filters.timeRange === "30D" ? 4 : 2))
    const created = Math.max(0, Math.round(dailyBase * spanDays * seasonal * (0.85 + rng() * 0.3)))
    const resolved = Math.max(0, Math.round(created * (0.82 + rng() * 0.22)))
    points.push({
      date: date.toISOString(),
      label: useDayLabel ? dayFormatter.format(date) : monthFormatter.format(date),
      created,
      resolved,
    })
  }
  return points
}

function distribute<T extends string>(
  rng: () => number,
  total: number,
  weights: Record<T, number>
): Record<T, number> {
  const keys = Object.keys(weights) as T[]
  const rawWeights = keys.map((k) => weights[k] * (0.85 + rng() * 0.3))
  const sum = rawWeights.reduce((s, w) => s + w, 0)
  const result = {} as Record<T, number>
  let allocated = 0
  keys.forEach((key, index) => {
    const isLast = index === keys.length - 1
    const value = isLast ? total - allocated : Math.round((rawWeights[index] / sum) * total)
    result[key] = Math.max(0, value)
    allocated += result[key]
  })
  return result
}

const statusWeights: Record<Status, number> = {
  OPEN: 0.18,
  IN_PROGRESS: 0.15,
  RESOLVED: 0.45,
  CLOSED: 0.17,
  TRANSFERRED: 0.05,
}

function getStatusDistribution(filters: AnalyticsFilters): Record<Status, number> {
  const rng = createSeededRandom(seedFor(filters, "status-dist"))
  const total = getKpiSnapshot(filters).totalTickets
  return distribute(rng, total, statusWeights)
}

const categoryWeights: Record<Category, number> = {
  Bug: 0.2,
  "Anomalie applicatif": 0.17,
  "Manque d'information": 0.09,
  "Assistance client": 0.15,
  "Bon usage": 0.07,
  vide: 0.03,
  "Synchronisation des données": 0.1,
  "Opération de service": 0.09,
  Habilitation: 0.06,
  "Hors périmètre": 0.04,
}

function getCategoryDistribution(filters: AnalyticsFilters): Record<Category, number> {
  const rng = createSeededRandom(seedFor(filters, "category-dist"))
  const total = getKpiSnapshot(filters).totalTickets
  return distribute(rng, total, categoryWeights)
}

const priorityWeights: Record<Priority, number> = {
  P1: 0.08,
  P2: 0.22,
  P3: 0.42,
  P4: 0.28,
}

function getPriorityDistribution(filters: AnalyticsFilters): Record<Priority, number> {
  const rng = createSeededRandom(seedFor(filters, "priority-dist"))
  const total = getKpiSnapshot(filters).totalTickets
  return distribute(rng, total, priorityWeights)
}

function getJiraMetrics(filters: AnalyticsFilters): JiraMetrics {
  const rng = createSeededRandom(seedFor(filters, "jira"))
  const total = getKpiSnapshot(filters).totalTickets
  const requiresJira = Math.max(1, Math.round(total * (0.12 + rng() * 0.08)))
  const transferredToJira = Math.round(requiresJira * (0.55 + rng() * 0.25))
  const awaitingDelivery = Math.max(
    0,
    Math.round((requiresJira - transferredToJira) * (0.4 + rng() * 0.3))
  )
  const avgDeliveryDelayDays = Math.round((3 + rng() * 9) * 10) / 10
  return { requiresJira, transferredToJira, awaitingDelivery, avgDeliveryDelayDays }
}

const attentionTitles = [
  "Rejeu du batch de règlement bloqué en file de reprise",
  "Rapport de rapprochement : lignes de fin de journée manquantes",
  "Export du grand livre tronqué pour les gros comptes",
  "Synchronisation des offres COLORIS en échec récurrent",
  "Habilitation manquante bloquant la clôture du dossier",
  "Anomalie sur le calcul de délai de livraison VIO",
]

const attentionAssignees = [
  "Camille Martin",
  "Luc Fontaine",
  "Amélie Moreau",
  "Kenji Nakamura",
  "Sade Okafor",
]

function getAttentionRequired(filters: AnalyticsFilters): AttentionRequired {
  const rng = createSeededRandom(seedFor(filters, "attention"))
  const thresholdDays = 6
  const count = randomInt(rng, 4, 14)
  const shown = Math.min(count, 5)

  const incidents: AgingIncident[] = Array.from({ length: shown }, (_, i) => ({
    ticketId: `TCK-${randomInt(rng, 10000, 99999)}`,
    title: attentionTitles[i % attentionTitles.length],
    ageDays: thresholdDays + randomInt(rng, 0, 21),
    priority: priorityOptions[randomInt(rng, 0, priorityOptions.length - 1)],
    assignee: attentionAssignees[randomInt(rng, 0, attentionAssignees.length - 1)],
  })).sort((a, b) => b.ageDays - a.ageDays)

  return { count, thresholdDays, incidents }
}

export {
  getKpiSnapshot,
  getActivityTrend,
  getStatusDistribution,
  getCategoryDistribution,
  getPriorityDistribution,
  getJiraMetrics,
  getAttentionRequired,
}
