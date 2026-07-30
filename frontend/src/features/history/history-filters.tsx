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
import { statusConfig } from "@/components/app/status"
import type { components } from "@/types/api"
import type { HistoryFilters } from "@/features/history/filter-history"
import {
  applicationOptions,
  completedStatusOptions,
  categoryOptions,
} from "@/features/tickets/constants"

type UserSummary = components["schemas"]["UserSummaryResponse"]

interface HistoryFiltersBarProps {
  filters: HistoryFilters
  onChange: (patch: Partial<HistoryFilters>) => void
  onReset: () => void
  assignees: UserSummary[]
}

function HistoryFiltersBar({ filters, onChange, onReset, assignees }: HistoryFiltersBarProps) {
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
      >
        <SelectTrigger className="w-[160px]">
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

      <div className="flex items-center gap-1.5">
        <span className="text-xs text-muted-foreground">Du</span>
        <Input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => onChange({ dateFrom: e.target.value })}
          className="w-[150px]"
        />
        <span className="text-xs text-muted-foreground">au</span>
        <Input
          type="date"
          value={filters.dateTo}
          onChange={(e) => onChange({ dateTo: e.target.value })}
          className="w-[150px]"
        />
      </div>

      <Button variant="ghost" size="sm" onClick={onReset}>
        <RotateCcw className="size-4" /> Réinitialiser
      </Button>
    </div>
  )
}

export { HistoryFiltersBar }
