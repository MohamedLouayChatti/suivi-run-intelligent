"use client"

import { useMemo, useState } from "react"
import { Search } from "lucide-react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { mockAuditEvents, type AuditResult } from "@/features/audit/mock-data"

const PAGE_SIZE = 10

const dateTimeFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
})

// Result reuses the app's existing themed success/destructive Badge variants
// (already desaturated for the palette, no border) instead of raw green/red —
// same treatment as the boolean flags in ticket-metadata-card.tsx.
const resultLabels: Record<AuditResult, string> = {
  SUCCESS: "Succès",
  DENIED: "Refusé",
}

function AuditLogTable() {
  const [query, setQuery] = useState("")
  const [result, setResult] = useState<"all" | AuditResult>("all")
  const [rawPage, setRawPage] = useState(1)

  const filtered = useMemo(
    () =>
      mockAuditEvents.filter(
        (e) =>
          (result === "all" || e.result === result) &&
          (query === "" ||
            (e.actor + e.action + e.target).toLowerCase().includes(query.toLowerCase()))
      ),
    [query, result]
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
            placeholder="Rechercher un acteur, une action ou une cible…"
            className="pl-9"
          />
        </div>
        <Select
          value={result}
          onValueChange={(v) => {
            setResult(v as "all" | AuditResult)
            setRawPage(1)
          }}
        >
          <SelectTrigger className="w-[11rem]"><SelectValue placeholder="Résultat" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les résultats</SelectItem>
            <SelectItem value="SUCCESS">Succès</SelectItem>
            <SelectItem value="DENIED">Refusé</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Horodatage</TableHead>
            <TableHead>Acteur</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Cible</TableHead>
            <TableHead>Origine</TableHead>
            <TableHead>Résultat</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.length === 0 ? (
            <TableRow className="hover:bg-transparent">
              <TableCell colSpan={6} className="py-8 text-center whitespace-normal text-sm text-muted-foreground">
                Aucun événement ne correspond à ces critères.
              </TableCell>
            </TableRow>
          ) : (
            rows.map((e) => (
              <TableRow key={e.id} className="hover:bg-transparent">
                <TableCell className="font-mono text-xs text-muted-foreground tabular">
                  {dateTimeFormatter.format(new Date(e.timestamp))}
                </TableCell>
                <TableCell className="font-medium">{e.actor}</TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">{e.action}</TableCell>
                <TableCell>{e.target}</TableCell>
                <TableCell className="font-mono text-xs text-muted-foreground">{e.origin}</TableCell>
                <TableCell>
                  <Badge variant={e.result === "SUCCESS" ? "success" : "destructive"}>
                    {resultLabels[e.result]}
                  </Badge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      <Pagination page={page} pageCount={pageCount} onPageChange={setRawPage} className="border-t border-border" />
    </SectionCard>
  )
}

export { AuditLogTable }
