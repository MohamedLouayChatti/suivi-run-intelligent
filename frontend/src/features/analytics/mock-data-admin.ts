import { timeRangeDays } from "@/features/analytics/constants"
import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"
import { createSeededRandom, randomInt } from "@/features/analytics/random"
import type {
  ApplicationHealth,
  AppMonthlyTrendPoint,
  AppWorkloadRow,
  EngineerDatum,
  HealthLevel,
} from "@/features/analytics/types"
import { applicationOptions } from "@/features/tickets/constants"

// No /analytics endpoint exists yet — mocked and isolated here for a later one-file
// swap. These generators back the "All Applications"-only admin sections: Cross
// Application Overview and Team Overview (§6 of the Analytics page). They ignore
// filters.application on purpose — those sections only render when "all" is selected.

function seedFor(timeRange: AnalyticsFilters["timeRange"], section: string): string {
  return `${section}:${timeRange}`
}

function scaleFor(timeRange: AnalyticsFilters["timeRange"]): number {
  return timeRangeDays[timeRange] / 30
}

function getWorkloadComparison(timeRange: AnalyticsFilters["timeRange"]): AppWorkloadRow[] {
  const rng = createSeededRandom(seedFor(timeRange, "workload"))
  const scale = scaleFor(timeRange)
  return applicationOptions.map((application) => ({
    application,
    open: Math.round(randomInt(rng, 10, 40) * scale),
    inProgress: Math.round(randomInt(rng, 8, 30) * scale),
    resolved: Math.round(randomInt(rng, 40, 120) * scale),
  }))
}

const healthLevels: HealthLevel[] = ["good", "warning", "critical"]

function getApplicationHealth(timeRange: AnalyticsFilters["timeRange"]): ApplicationHealth[] {
  const rng = createSeededRandom(seedFor(timeRange, "health"))
  const scale = scaleFor(timeRange)
  return applicationOptions.map((application) => {
    const roll = rng()
    const health = roll < 0.55 ? healthLevels[0] : roll < 0.85 ? healthLevels[1] : healthLevels[2]
    return {
      application,
      health,
      activeTickets: Math.round(randomInt(rng, 15, 60) * scale),
      avgResolutionHours: Math.round((6 + rng() * 36) * 10) / 10,
      urgentTickets: randomInt(rng, 0, 9),
    }
  })
}

function getResolutionTimeComparison(
  timeRange: AnalyticsFilters["timeRange"]
): { application: (typeof applicationOptions)[number]; avgResolutionHours: number }[] {
  const rng = createSeededRandom(seedFor(timeRange, "resolution-time"))
  return applicationOptions
    .map((application) => ({
      application,
      avgResolutionHours: Math.round((6 + rng() * 36) * 10) / 10,
    }))
    .sort((a, b) => b.avgResolutionHours - a.avgResolutionHours)
}

function getJiraDependency(
  timeRange: AnalyticsFilters["timeRange"]
): { application: (typeof applicationOptions)[number]; jiraIncidents: number }[] {
  const rng = createSeededRandom(seedFor(timeRange, "jira-dependency"))
  const scale = scaleFor(timeRange)
  return applicationOptions
    .map((application) => ({
      application,
      jiraIncidents: Math.round(randomInt(rng, 3, 45) * scale),
    }))
    .sort((a, b) => b.jiraIncidents - a.jiraIncidents)
}

function getTransferRate(
  timeRange: AnalyticsFilters["timeRange"]
): { application: (typeof applicationOptions)[number]; transferRatePct: number }[] {
  const rng = createSeededRandom(seedFor(timeRange, "transfer-rate"))
  return applicationOptions
    .map((application) => ({
      application,
      transferRatePct: Math.round((2 + rng() * 14) * 10) / 10,
    }))
    .sort((a, b) => b.transferRatePct - a.transferRatePct)
}

const monthFormatter = new Intl.DateTimeFormat("fr-FR", { month: "short" })

function getMonthlyTrends(timeRange: AnalyticsFilters["timeRange"]): AppMonthlyTrendPoint[] {
  const rng = createSeededRandom(seedFor(timeRange, "monthly-trends"))
  const points: AppMonthlyTrendPoint[] = []
  for (let i = 11; i >= 0; i--) {
    const date = new Date(Date.now() - i * 30 * 24 * 60 * 60 * 1000)
    points.push({
      month: monthFormatter.format(date),
      FCI: randomInt(rng, 60, 140),
      COLORIS: randomInt(rng, 40, 110),
      AERO: randomInt(rng, 20, 70),
      VIO: randomInt(rng, 80, 170),
    })
  }
  return points
}

const engineers = [
  "Camille Martin",
  "Luc Fontaine",
  "Amélie Moreau",
  "Kenji Nakamura",
  "Sade Okafor",
  "Yanis Belkacem",
]

function getActiveTicketsPerEngineer(timeRange: AnalyticsFilters["timeRange"]): EngineerDatum[] {
  const rng = createSeededRandom(seedFor(timeRange, "active-per-engineer"))
  return engineers
    .map((engineer) => ({ engineer, value: randomInt(rng, 3, 22) }))
    .sort((a, b) => b.value - a.value)
}

function getResolvedTicketsPerEngineer(timeRange: AnalyticsFilters["timeRange"]): EngineerDatum[] {
  const rng = createSeededRandom(seedFor(timeRange, "resolved-per-engineer"))
  const scale = scaleFor(timeRange)
  return engineers.map((engineer) => ({
    engineer,
    value: Math.round(randomInt(rng, 8, 40) * scale),
  }))
}

function getAvgResolutionPerEngineer(timeRange: AnalyticsFilters["timeRange"]): EngineerDatum[] {
  const rng = createSeededRandom(seedFor(timeRange, "avg-resolution-per-engineer"))
  return engineers
    .map((engineer) => ({ engineer, value: Math.round((5 + rng() * 30) * 10) / 10 }))
    .sort((a, b) => a.value - b.value)
}

function getAssignmentDistribution(timeRange: AnalyticsFilters["timeRange"]): EngineerDatum[] {
  const rng = createSeededRandom(seedFor(timeRange, "assignment-distribution"))
  return engineers.map((engineer) => ({ engineer, value: randomInt(rng, 12, 55) }))
}

function getTransferRatePerEngineer(timeRange: AnalyticsFilters["timeRange"]): EngineerDatum[] {
  const rng = createSeededRandom(seedFor(timeRange, "transfer-rate-per-engineer"))
  return engineers
    .map((engineer) => ({ engineer, value: Math.round((1 + rng() * 12) * 10) / 10 }))
    .sort((a, b) => b.value - a.value)
}

export {
  getWorkloadComparison,
  getApplicationHealth,
  getResolutionTimeComparison,
  getJiraDependency,
  getTransferRate,
  getMonthlyTrends,
  getActiveTicketsPerEngineer,
  getResolvedTicketsPerEngineer,
  getAvgResolutionPerEngineer,
  getAssignmentDistribution,
  getTransferRatePerEngineer,
}
