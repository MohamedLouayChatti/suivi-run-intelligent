"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { applicationOptions } from "@/features/tickets/constants"
import { timeRangeOptions, timeRangeLabels } from "@/features/analytics/constants"
import type { AnalyticsFilters } from "@/features/analytics/filter-analytics"

interface AnalyticsFilterControlsProps {
  filters: AnalyticsFilters
  onChange: (patch: Partial<AnalyticsFilters>) => void
}

// Rendered inside the page header's actions slot — later becomes permission-aware
// (application choices narrowed to the authenticated user's assignments).
function AnalyticsFilterControls({ filters, onChange }: AnalyticsFilterControlsProps) {
  return (
    <>
      <Select
        value={filters.application}
        onValueChange={(value) => onChange({ application: value as AnalyticsFilters["application"] })}
      >
        <SelectTrigger className="w-[170px]">
          <SelectValue placeholder="Application" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Toutes les applications</SelectItem>
          {applicationOptions.map((app) => (
            <SelectItem key={app} value={app}>
              {app}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.timeRange}
        onValueChange={(value) => onChange({ timeRange: value as AnalyticsFilters["timeRange"] })}
      >
        <SelectTrigger className="w-[170px]">
          <SelectValue placeholder="Période" />
        </SelectTrigger>
        <SelectContent>
          {timeRangeOptions.map((range) => (
            <SelectItem key={range} value={range}>
              {timeRangeLabels[range]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </>
  )
}

export { AnalyticsFilterControls }
