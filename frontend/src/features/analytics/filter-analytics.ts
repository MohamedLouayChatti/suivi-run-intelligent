import type { components } from "@/types/api"
import type { TimeRange } from "@/features/analytics/constants"

type Application = components["schemas"]["Application"]

interface AnalyticsFilters {
  application: Application | "all"
  timeRange: TimeRange
}

const defaultAnalyticsFilters: AnalyticsFilters = {
  application: "all",
  timeRange: "30D",
}

export { defaultAnalyticsFilters }
export type { AnalyticsFilters }
