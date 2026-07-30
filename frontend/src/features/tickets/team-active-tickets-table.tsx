"use client"

import { useMemo, useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { TicketsTable } from "@/features/tickets/ticket-table"
import { applyTicketFilters, type TicketFilters } from "@/features/tickets/filter-tickets"
import { currentUserId } from "@/features/tickets/mock-data"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

const PAGE_SIZE = 5

interface TeamActiveTicketsTableProps {
  tickets: TicketDetail[]
  filters: TicketFilters
  isLoading: boolean
}

function TeamActiveTicketsTable({ tickets, filters, isLoading }: TeamActiveTicketsTableProps) {
  const [rawPage, setRawPage] = useState(1)

  const filtered = useMemo(
    () => applyTicketFilters(tickets, filters).filter((t) => t.assignee?.id !== currentUserId),
    [tickets, filters]
  )
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const page = Math.min(rawPage, pageCount)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <SectionCard
      title="Tickets actifs de l'équipe"
      description="Tickets actifs affectés à vos collègues."
      bodyClassName="p-0"
    >
      <TicketsTable
        tickets={paged}
        isLoading={isLoading}
        showAssignee
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

export { TeamActiveTicketsTable }
