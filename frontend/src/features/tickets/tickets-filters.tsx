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
import type { TicketFilters } from "@/features/tickets/filter-tickets"
import {
  priorityOptions,
  activeStatusOptions,
  categoryOptions,
} from "@/features/tickets/constants"

type UserSummary = components["schemas"]["UserSummaryResponse"]
type Application = components["schemas"]["Application"]

interface TicketsFiltersProps {
  filters: TicketFilters
  onChange: (patch: Partial<TicketFilters>) => void
  onReset: () => void
  assignees: UserSummary[]
  /** The user's own applications (primary, + backup if any) — never the full 4-app list;
   * a user can only ever see tickets from applications they're assigned to. */
  accessibleApplications: Application[]
  /** Only admins may filter by ingénieur — GET /auth/users 403s for anyone else. */
  showAssigneeFilter: boolean
}

function TicketsFilters({ filters, onChange, onReset, assignees, accessibleApplications, showAssigneeFilter }: TicketsFiltersProps) {
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
        onValueChange={(value) => onChange({ application: value as TicketFilters["application"] })}
        disabled={accessibleApplications.length < 2}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Application" />
        </SelectTrigger>
        <SelectContent>
          {accessibleApplications.length > 1 && (
            <SelectItem value="all">Toutes mes applications</SelectItem>
          )}
          {accessibleApplications.map((app) => (
            <SelectItem key={app} value={app}>
              {app}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.priority}
        onValueChange={(value) => onChange({ priority: value as TicketFilters["priority"] })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Priorité" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Toutes les priorités</SelectItem>
          {priorityOptions.map((p) => (
            <SelectItem key={p} value={p}>
              {p}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.status}
        onValueChange={(value) => onChange({ status: value as TicketFilters["status"] })}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Statut" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tous les statuts</SelectItem>
          {activeStatusOptions.map((s) => (
            <SelectItem key={s} value={s}>
              {statusConfig[s].label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {showAssigneeFilter && (
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
      )}

      <Select
        value={filters.category}
        onValueChange={(value) => onChange({ category: value as TicketFilters["category"] })}
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

      <Button variant="ghost" size="sm" onClick={onReset}>
        <RotateCcw className="size-4" /> Réinitialiser
      </Button>
    </div>
  )
}

export { TicketsFilters }
