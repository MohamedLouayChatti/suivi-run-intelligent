"use client"

import { useMemo, useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { TicketsTable, type DateColumn } from "@/features/tickets/ticket-table"
import { applyHistoryFilters, getCompletedAt, type HistoryFilters } from "@/features/history/filter-history"
import type { components } from "@/types/api"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]

const PAGE_SIZE = 10

const completedAtColumn: DateColumn[] = [{ label: "Complété le", getValue: getCompletedAt }]

interface HistoryTableProps {
  tickets: TicketSummary[]
  filters: HistoryFilters
  isLoading: boolean
}

function HistoryTable({ tickets, filters, isLoading }: HistoryTableProps) {
  const [rawPage, setRawPage] = useState(1)

  const filtered = useMemo(() => applyHistoryFilters(tickets, filters), [tickets, filters])
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const page = Math.min(rawPage, pageCount)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <SectionCard
      title="Tickets complétés"
      description="Incidents clôturés ou transférés, triés par date de complétion."
      bodyClassName="p-0"
    >
      <TicketsTable
        tickets={paged}
        isLoading={isLoading}
        showAssignee
        showPriority={false}
        dateColumns={completedAtColumn}
        emptyMessage="Aucun ticket complété ne correspond à vos filtres."
      />
      <Pagination
        page={page}
        pageCount={pageCount}
        onPageChange={setRawPage}
        className="border-t border-border"
      />
    </SectionCard>
  )
}

export { HistoryTable }
