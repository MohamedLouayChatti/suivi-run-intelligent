"use client"

import { useMemo, useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { TicketsTable } from "@/features/tickets/ticket-table"
import { applyTicketFilters, type TicketFilters } from "@/features/tickets/filter-tickets"
import type { components } from "@/types/api"

type TicketSummary = components["schemas"]["TicketSummaryResponse"]

const PAGE_SIZE = 5

interface MyActiveTicketsTableProps {
  tickets: TicketSummary[]
  filters: TicketFilters
  isLoading: boolean
  currentUserId: string
}

function MyActiveTicketsTable({ tickets, filters, isLoading, currentUserId }: MyActiveTicketsTableProps) {
  const [rawPage, setRawPage] = useState(1)

  const filtered = useMemo(
    () => applyTicketFilters(tickets, filters).filter((t) => t.assignee?.id === currentUserId),
    [tickets, filters, currentUserId]
  )
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const page = Math.min(rawPage, pageCount)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <SectionCard
      title="Mes tickets actifs"
      description="Tickets qui vous sont affectés, ouverts, en cours ou résolus."
      bodyClassName="p-0"
    >
      <TicketsTable
        tickets={paged}
        isLoading={isLoading}
        showAssignee={false}
        emptyMessage="Aucun ticket actif ne correspond à ces filtres."
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

export { MyActiveTicketsTable }
