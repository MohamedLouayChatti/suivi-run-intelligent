import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"
import { AeroInsights } from "@/features/analytics/insights/aero-insights"
import { ColorisHeatmap } from "@/features/analytics/insights/coloris-heatmap"
import { VioInsights } from "@/features/analytics/insights/vio-insights"
import {
  getAeroTopElements,
  getColorisHeatmap,
  getVioAppRows,
} from "@/features/analytics/mock-data-insights"

interface ApplicationInsightsProps {
  filters: AnalyticsFilters
}

// FCI has no additional widgets (renders nothing). "all" is handled separately by the
// admin-only Cross Application Overview + Team Overview sections in the page itself.
function ApplicationInsights({ filters }: ApplicationInsightsProps) {
  if (filters.application === "COLORIS") {
    return <ColorisHeatmap cells={getColorisHeatmap(filters)} />
  }
  if (filters.application === "AERO") {
    return <AeroInsights topElements={getAeroTopElements(filters)} />
  }
  if (filters.application === "VIO") {
    return <VioInsights rows={getVioAppRows(filters)} />
  }
  return null
}

export { ApplicationInsights }
