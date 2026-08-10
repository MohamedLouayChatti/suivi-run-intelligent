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
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

interface AnalyticsFilterControlsProps {
  filters: AnalyticsFilters
  onChange: (patch: Partial<AnalyticsFilters>) => void
  /** Hard admin-role gate — only admins may see cross-application ("Toutes les applications")
   * analytics; everyone else is scoped to their own assignments. */
  canReadAllApplications: boolean
  /** The user's own applications (primary, + backup if any) — ignored for admins, who choose
   * from every application instead. */
  accessibleApplications: Application[]
}

// Rendered inside the page header's actions slot.
function AnalyticsFilterControls({
  filters,
  onChange,
  canReadAllApplications,
  accessibleApplications,
}: AnalyticsFilterControlsProps) {
  return (
    <>
      <Select
        value={filters.application}
        onValueChange={(value) => onChange({ application: value as AnalyticsFilters["application"] })}
        disabled={!canReadAllApplications && accessibleApplications.length < 2}
      >
        <SelectTrigger className="w-[170px]">
          <SelectValue placeholder="Application" />
        </SelectTrigger>
        <SelectContent>
          {canReadAllApplications ? (
            <>
              <SelectItem value="all">Toutes les applications</SelectItem>
              {applicationOptions.map((app) => (
                <SelectItem key={app} value={app}>
                  {app}
                </SelectItem>
              ))}
            </>
          ) : (
            accessibleApplications.map((app) => (
              <SelectItem key={app} value={app}>
                {app}
              </SelectItem>
            ))
          )}
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
