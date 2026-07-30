"use client"

import { useRouter } from "next/navigation"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { StatusBadge, PriorityBadge } from "@/components/app/status"
import type { components } from "@/types/api"

// Detail is a superset of Summary (adds closed_at/resolved_at/etc.) and every current data
// source already hands the table full detail objects, so the table type is widened here
// rather than plumbing an extra field through TicketSummaryResponse.
type TicketRow = components["schemas"]["TicketDetailResponse"]

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
})

interface DateColumn {
  label: string
  getValue: (ticket: TicketRow) => string
}

const defaultDateColumns: DateColumn[] = [
  { label: "Créé", getValue: (t) => t.created_at },
  { label: "Mis à jour", getValue: (t) => t.updated_at },
]

interface TicketsTableProps {
  tickets: TicketRow[]
  isLoading: boolean
  showAssignee: boolean
  emptyMessage: string
  showPriority?: boolean
  dateColumns?: DateColumn[]
}

function TicketsTable({
  tickets,
  isLoading,
  showAssignee,
  emptyMessage,
  showPriority = true,
  dateColumns = defaultDateColumns,
}: TicketsTableProps) {
  const router = useRouter()
  const columnCount =
    2 + (showPriority ? 1 : 0) + 1 + (showAssignee ? 1 : 0) + 1 + dateColumns.length

  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead>ID</TableHead>
          <TableHead>Titre</TableHead>
          {showPriority && <TableHead>Priorité</TableHead>}
          <TableHead>Statut</TableHead>
          {showAssignee && <TableHead>Assigné à</TableHead>}
          <TableHead>Application</TableHead>
          {dateColumns.map((col) => (
            <TableHead key={col.label}>{col.label}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <TableRow key={i} className="hover:bg-transparent">
              {Array.from({ length: columnCount + 1 }).map((_, j) => (
                <TableCell key={j}>
                  <Skeleton className="h-4 w-full max-w-24" />
                </TableCell>
              ))}
            </TableRow>
          ))
        ) : tickets.length === 0 ? (
          <TableRow className="hover:bg-transparent">
            <TableCell
              colSpan={columnCount + 1}
              className="py-8 text-center whitespace-normal text-sm text-muted-foreground"
            >
              {emptyMessage}
            </TableCell>
          </TableRow>
        ) : (
          tickets.map((t) => (
            <TableRow
              key={t.id}
              className="cursor-pointer"
              onClick={() => router.push(`/tickets/${t.id}`)}
            >
              <TableCell className="font-mono text-xs text-muted-foreground">
                {t.id.slice(0, 8)}
              </TableCell>
              <TableCell className="max-w-[320px] truncate font-medium">{t.title}</TableCell>
              {showPriority && (
                <TableCell>
                  <PriorityBadge priority={t.priority} />
                </TableCell>
              )}
              <TableCell>
                <StatusBadge status={t.status} />
              </TableCell>
              {showAssignee && (
                <TableCell className="text-sm">{t.assignee?.display_name ?? "—"}</TableCell>
              )}
              <TableCell className="text-sm text-muted-foreground">{t.application}</TableCell>
              {dateColumns.map((col) => (
                <TableCell key={col.label} className="text-sm text-muted-foreground">
                  {dateFormatter.format(new Date(col.getValue(t)))}
                </TableCell>
              ))}
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
}

export { TicketsTable }
export type { DateColumn }
