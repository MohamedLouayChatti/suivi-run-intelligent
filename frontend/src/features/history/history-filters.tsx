"use client"

import { RotateCcw, Search } from "lucide-react"

import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { DateRangeFilter } from "@/components/app/date-range-filter"
import { statusConfig } from "@/components/app/status"
import type { components } from "@/types/api"
import { HISTORY_MIN_DATE, type HistoryFilters } from "@/features/history/filter-history"
import {
  applicationOptions,
  completedStatusOptions,
  categoryOptions,
} from "@/features/tickets/constants"

type UserDirectory = components["schemas"]["UserDirectoryResponse"]
type Application = components["schemas"]["Application"]

interface HistoryFiltersBarProps {
  filters: HistoryFilters
  onChange: (patch: Partial<HistoryFilters>) => void
  onReset: () => void
  assignees: UserDirectory[]
  /** Mirrors the backend's ticket application scope: holding `ticket.read_any_application` is
   * what lets a caller span every application, rather than belonging to any particular role.
   * `GET /tickets` already returns every application's tickets to such a caller, so this only
   * decides whether the filter offers them as choices. */
  canReadAllApplications: boolean
  /** The user's own applications (primary, + backup if any) — ignored when the caller holds the
   * breadth permission above, who chooses from every application instead. */
  accessibleApplications: Application[]
}

function HistoryFiltersBar({
  filters,
  onChange,
  onReset,
  assignees,
  canReadAllApplications,
  accessibleApplications,
}: HistoryFiltersBarProps) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-card p-4">
      <div className="relative min-w-[220px] flex-1">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value })}
          placeholder="Rechercher un ticket, un identifiant…"
          className="pl-8"
        />
      </div>

      <Select
        value={filters.application}
        onValueChange={(value) => onChange({ application: value as HistoryFilters["application"] })}
        disabled={!canReadAllApplications && accessibleApplications.length < 2}
      >
        <SelectTrigger className="w-[180px]">
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
            <>
              {accessibleApplications.length > 1 && (
                <SelectItem value="all">Toutes mes applications</SelectItem>
              )}
              {accessibleApplications.map((app) => (
                <SelectItem key={app} value={app}>
                  {app}
                </SelectItem>
              ))}
            </>
          )}
        </SelectContent>
      </Select>

      <Select
        value={filters.status}
        onValueChange={(value) => onChange({ status: value as HistoryFilters["status"] })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Statut" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tous les statuts</SelectItem>
          {completedStatusOptions.map((s) => (
            <SelectItem key={s} value={s}>
              {statusConfig[s].label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.assigneeId}
        onValueChange={(value) => onChange({ assigneeId: value })}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Ingénieur affecté" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tous les ingénieurs</SelectItem>
          {assignees.map((a) => (
            <SelectItem key={a.id} value={a.id}>
              {a.display_name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.category}
        onValueChange={(value) => onChange({ category: value as HistoryFilters["category"] })}
      >
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Catégorie" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Toutes les catégories</SelectItem>
          {categoryOptions.map((c) => (
            <SelectItem key={c} value={c}>
              {c}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <DateRangeFilter
        value={{ from: filters.dateFrom, to: filters.dateTo }}
        onChange={(range) => onChange({ dateFrom: range.from, dateTo: range.to })}
        minDate={HISTORY_MIN_DATE}
        placeholder="Période"
        className="w-[240px]"
      />

      <Button variant="ghost" size="sm" onClick={onReset}>
        <RotateCcw className="size-4" /> Réinitialiser
      </Button>
    </div>
  )
}

export { HistoryFiltersBar }
