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

type TicketSummary = components["schemas"]["TicketSummaryResponse"]

const dateFormatter = new Intl.DateTimeFormat("fr-FR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
})

interface TicketsTableProps {
  tickets: TicketSummary[]
  isLoading: boolean
  showAssignee: boolean
  emptyMessage: string
}

function TicketsTable({ tickets, isLoading, showAssignee, emptyMessage }: TicketsTableProps) {
  const router = useRouter()
  const columnCount = showAssignee ? 7 : 6

  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead>ID</TableHead>
          <TableHead>Titre</TableHead>
          <TableHead>Priorité</TableHead>
          <TableHead>Statut</TableHead>
          {showAssignee && <TableHead>Assigné à</TableHead>}
          <TableHead>Application</TableHead>
          <TableHead>Créé</TableHead>
          <TableHead>Mis à jour</TableHead>
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
              <TableCell>
                <PriorityBadge priority={t.priority} />
              </TableCell>
              <TableCell>
                <StatusBadge status={t.status} />
              </TableCell>
              {showAssignee && (
                <TableCell className="text-sm">{t.assignee?.display_name ?? "—"}</TableCell>
              )}
              <TableCell className="text-sm text-muted-foreground">{t.application}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {dateFormatter.format(new Date(t.created_at))}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {dateFormatter.format(new Date(t.updated_at))}
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  )
}

export { TicketsTable }
