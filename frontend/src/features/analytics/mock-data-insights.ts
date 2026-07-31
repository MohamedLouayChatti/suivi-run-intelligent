import { timeRangeDays } from "@/features/analytics/constants"
import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"
import { createSeededRandom, randomInt } from "@/features/analytics/random"
import type { ColorisHeatmapCell, RankedEntry, VioAppRow } from "@/features/analytics/types"
import { elementOptions, offerOptions, versionOptions, vioAppOptions } from "@/features/tickets/constants"

// No /analytics endpoint exists yet — mocked and isolated here for a later one-file
// swap, same convention as mock-data.ts. These generators back the per-application
// "Application Insights" widgets (§6 of the Analytics page).

function seedFor(filters: AnalyticsFilters, section: string): string {
  return `${section}:${filters.application}:${filters.timeRange}`
}

function scaleFor(filters: AnalyticsFilters): number {
  return timeRangeDays[filters.timeRange] / 30
}

// COLORIS: rows = Offers, columns = Versions — replaces the historical Excel matrix.
// Only the most common offer codes are shown, matching the offer select in tickets/constants.ts.
const heatmapOffers = offerOptions.slice(0, 8)

function getColorisHeatmap(filters: AnalyticsFilters): ColorisHeatmapCell[] {
  const rng = createSeededRandom(seedFor(filters, "coloris-heatmap"))
  const scale = scaleFor(filters)
  const cells: ColorisHeatmapCell[] = []
  for (const offer of heatmapOffers) {
    for (const version of versionOptions) {
      const isHotspot = rng() < 0.25
      const base = isHotspot ? randomInt(rng, 8, 22) : randomInt(rng, 0, 6)
      cells.push({ offer, version, count: Math.round(base * scale) })
    }
  }
  return cells
}

function getAeroTopElements(filters: AnalyticsFilters): RankedEntry[] {
  const rng = createSeededRandom(seedFor(filters, "aero-elements"))
  const scale = scaleFor(filters)
  return elementOptions
    .map((element) => ({ label: element, count: Math.round(randomInt(rng, 3, 40) * scale) }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 7)
}

function getVioAppRows(filters: AnalyticsFilters): VioAppRow[] {
  const rng = createSeededRandom(seedFor(filters, "vio-apps"))
  const scale = scaleFor(filters)
  return vioAppOptions.map((vioApp) => {
    const open = Math.round(randomInt(rng, 4, 18) * scale)
    const resolved = Math.round(randomInt(rng, 20, 60) * scale)
    return { vioApp, open, resolved, total: open + resolved }
  })
}

export { getColorisHeatmap, getAeroTopElements, getVioAppRows }
