"use client"

import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
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

const moduleLabels: Record<string, string> = {
  ticket_management: "Tickets",
  auth: "Auth",
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
  const [rawPage, setRawPage] = useState(1)

  const { data: entries = [], isLoading } = useQuery({
    queryKey: auditListQueryKey,
    queryFn: () => listAuditEntries(),
  })

  const modules = useMemo(() => [...new Set(entries.map((e) => e.module))].sort(), [entries])

  const filtered = useMemo(
    () =>
      entries.filter(
        (e) =>
          (moduleFilter === "all" || e.module === moduleFilter) &&
          (query === "" ||
            (getActorLabel(e) + e.action + e.resource_type).toLowerCase().includes(query.toLowerCase()))
      ),
    [entries, query, moduleFilter]
  )

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const page = Math.min(rawPage, pageCount)
  const rows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <SectionCard bodyClassName="p-0">
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        <div className="relative min-w-0 flex-1 basis-64">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" strokeWidth={1.75} />
          <Input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setRawPage(1)
            }}
            placeholder="Rechercher un acteur, une action ou une ressource…"
            className="pl-9"
          />
        </div>
        <Select
          value={moduleFilter}
          onValueChange={(v) => {
            onModuleFilterChange(v)
            setRawPage(1)
          }}
        >
          <SelectTrigger className="w-[11rem]"><SelectValue placeholder="Module" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les modules</SelectItem>
            {modules.map((m) => (
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
              return (
                <TableRow key={e.id} className="hover:bg-transparent">
                  <TableCell className="font-mono text-xs text-muted-foreground tabular">
                    {dateTimeFormatter.format(new Date(e.occurred_at))}
                  </TableCell>
                  <TableCell className="font-medium">{getActorLabel(e)}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">{e.action}</TableCell>
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
      <Pagination page={page} pageCount={pageCount} onPageChange={setRawPage} className="border-t border-border" />
    </SectionCard>
  )
}

export { AuditLogTable }
