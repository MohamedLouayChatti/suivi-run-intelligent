import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"
import { AeroInsights } from "@/features/analytics/insights/aero-insights"
import { ColorisHeatmap } from "@/features/analytics/insights/coloris-heatmap"
import { VioInsights } from "@/features/analytics/insights/vio-insights"
import { useApplicationInsights } from "@/features/analytics/use-analytics"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

interface ApplicationInsightsProps {
  filters: AnalyticsFilters
}

// FCI has no additional widgets (renders nothing). "all" is handled separately by the
// admin-only Cross Application Overview + Team Overview sections in the page itself.
function ApplicationInsights({ filters }: ApplicationInsightsProps) {
  const { application } = filters
  const insightsApplication: Application | null =
    application === "COLORIS" || application === "AERO" || application === "VIO" ? application : null

  const { data } = useApplicationInsights(insightsApplication, filters.timeRange)

  if (!insightsApplication || !data) return null

  if (insightsApplication === "COLORIS" && data.coloris_heatmap) {
    return <ColorisHeatmap cells={data.coloris_heatmap} />
  }
  if (insightsApplication === "AERO" && data.aero_top_elements) {
    return <AeroInsights topElements={data.aero_top_elements} />
  }
  if (insightsApplication === "VIO" && data.vio_app_rows) {
    return <VioInsights rows={data.vio_app_rows} />
  }
  return null
}

export { ApplicationInsights }
