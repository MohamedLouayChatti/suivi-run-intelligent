"use client"

import { useEffect, useMemo, useState } from "react"
import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { Search } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { listAuditEntries, type AuditEntry } from "@/services/api/audit"

import { auditListQueryKey } from "./query-keys"

const PAGE_SIZE = 10

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
})

// The modules that actually publish audited events (see Audit's CLAUDE.md) -- fixed and
// small, so this is a plain constant rather than derived from whatever page of entries
// happens to be loaded. Deriving it from the fetched page broke once that page became
// filtered by module server-side: filtering to one module would then leave only that one
// module in the set the dropdown offers to switch to.
const moduleLabels: Record<string, string> = {
  ticket_management: "Tickets",
  auth: "Auth",
  knowledge_base: "Base de connaissances",
}
const auditedModules = Object.keys(moduleLabels)

// Every `action` the backend sends is "<resource>.<verb>" (see AuditMapper) -- split once here
// so the column can render it over two lines instead of forcing the whole table to scroll.
function splitAction(action: string): { resource: string; verb: string } {
  const dotIndex = action.indexOf(".")
  if (dotIndex === -1) return { resource: action, verb: "" }
  return { resource: action.slice(0, dotIndex), verb: action.slice(dotIndex + 1) }
}

/** GET /audit always includes ticket_id/user_id/role_id/... under `<resource_type>_id`
 * (see AuditMapper) -- this is the one key every payload shape agrees on. */
function getResourceId(entry: AuditEntry): string | null {
  if (!entry.resource_type) return null
  const value = entry.payload[`${entry.resource_type}_id`]
  return typeof value === "string" ? value : null
}

function getActorLabel(entry: AuditEntry): string {
  return entry.actor?.display_name ?? entry.actor_label ?? "—"
}

interface AuditLogTableProps {
  moduleFilter: "all" | string
  onModuleFilterChange: (value: "all" | string) => void
}

function AuditLogTable({ moduleFilter, onModuleFilterChange }: AuditLogTableProps) {
  const [query, setQuery] = useState("")
  const [page, setPage] = useState(1)

  useEffect(() => setPage(1), [moduleFilter])

  const { data, isLoading } = useQuery({
    queryKey: [...auditListQueryKey, moduleFilter, page] as const,
    queryFn: () => listAuditEntries({ module: moduleFilter, page, pageSize: PAGE_SIZE }),
    placeholderData: keepPreviousData,
  })

  const entries = data?.items ?? []
  const total = data?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  // Module and pagination are real server-side filters now (GET /audit). The free-text box
  // stays a client-side refinement over whatever page that returns -- it matches actor
  // display name, which only exists after a separate cross-module lookup into Auth's user
  // directory and has no single-query server-side equivalent the way `module` does, so this
  // narrows within the current page rather than across the whole filtered result.
  const rows = useMemo(
    () =>
      entries.filter(
        (e) =>
          query === "" ||
          (getActorLabel(e) + e.action + e.resource_type).toLowerCase().includes(query.toLowerCase())
      ),
    [entries, query]
  )

  return (
    <SectionCard bodyClassName="p-0">
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <div className="relative min-w-0 flex-1 basis-64">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" strokeWidth={1.75} />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Rechercher un acteur, une action ou une ressource…"
            className="pl-9"
          />
        </div>
        <Select value={moduleFilter} onValueChange={onModuleFilterChange}>
          <SelectTrigger className="w-[11rem]"><SelectValue placeholder="Module" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les modules</SelectItem>
            {auditedModules.map((m) => (
              <SelectItem key={m} value={m}>{moduleLabels[m] ?? m}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Horodatage</TableHead>
            <TableHead>Acteur</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Module</TableHead>
            <TableHead>Ressource</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i} className="hover:bg-transparent">
                {Array.from({ length: 5 }).map((_, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full max-w-24" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          ) : rows.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={5} className="py-8 text-center whitespace-normal text-sm text-muted-foreground">
                Aucun événement ne correspond à ces critères.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((e) => {
              const resourceId = getResourceId(e)
              const { resource: actionResource, verb: actionVerb } = splitAction(e.action)
              return (
                <TableRow key={e.id} className="hover:bg-transparent">
                  <TableCell className="font-mono text-xs text-muted-foreground tabular">
                    {dateTimeFormatter.format(new Date(e.occurred_at))}
                  </TableCell>
                  <TableCell className="font-medium">{getActorLabel(e)}</TableCell>
                  <TableCell className="font-mono text-xs leading-tight text-muted-foreground">
                    <span className="block">{actionResource}/</span>
                    <span className="block">{actionVerb}</span>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{moduleLabels[e.module] ?? e.module}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {e.resource_type ?? "—"}
                    {resourceId ? ` · ${resourceId.slice(0, 8)}` : ""}
                  </TableCell>
                </TableRow>
              )
            })
          )}
        </TableBody>
      </Table>
      <Pagination page={Math.min(page, pageCount)} pageCount={pageCount} onPageChange={setPage} className="border-t border-border" />
    </SectionCard>
  )
}

export { AuditLogTable }
