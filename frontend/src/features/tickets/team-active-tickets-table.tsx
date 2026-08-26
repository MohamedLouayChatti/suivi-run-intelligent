"use client"

import { useEffect, useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { TicketsTable } from "@/features/tickets/ticket-table"
import { useActiveTickets } from "@/features/tickets/use-tickets-list"
import type { TicketFilters } from "@/features/tickets/filter-tickets"

const PAGE_SIZE = 5

interface TeamActiveTicketsTableProps {
  filters: TicketFilters
  currentUserId: string
}

function TeamActiveTicketsTable({ filters, currentUserId }: TeamActiveTicketsTableProps) {
  const [page, setPage] = useState(1)

  useEffect(() => setPage(1), [filters])

  const { tickets, total, isLoading } = useActiveTickets({
    filters,
    page,
    pageSize: PAGE_SIZE,
    assigneeId: filters.assigneeId === "all" ? undefined : filters.assigneeId,
    excludeAssigneeId: currentUserId,
    enabled: Boolean(currentUserId),
  })

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <SectionCard
      title="Tickets actifs de l'équipe"
      description="Tickets actifs affectés à vos collègues."
      bodyClassName="p-0"
    >
      <TicketsTable
        tickets={tickets}
        isLoading={isLoading}
        showAssignee
        emptyMessage="Aucun ticket actif ne correspond à ces filtres."
      />
      <Pagination
        page={Math.min(page, pageCount)}
        pageCount={pageCount}
        onPageChange={setPage}
        className="border-t border-border"
      />
    </SectionCard>
  )
}

export { TeamActiveTicketsTable }
