"use client"

import { useEffect, useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { TicketsTable } from "@/features/tickets/ticket-table"
import { useActiveTickets } from "@/features/tickets/use-tickets-list"
import type { TicketFilters } from "@/features/tickets/filter-tickets"

const PAGE_SIZE = 5

interface MyActiveTicketsTableProps {
  filters: TicketFilters
  currentUserId: string
}

function MyActiveTicketsTable({ filters, currentUserId }: MyActiveTicketsTableProps) {
  const [page, setPage] = useState(1)

  useEffect(() => setPage(1), [filters])

  // "Assigned to me" and the assignee filter are both equality constraints on the same
  // column -- if the filter names someone else, the two can never both hold, so there is
  // nothing to fetch rather than a request that can only come back empty.
  const matchesAssigneeFilter = filters.assigneeId === "all" || filters.assigneeId === currentUserId
  const enabled = Boolean(currentUserId) && matchesAssigneeFilter

  const { tickets, total, isLoading } = useActiveTickets({
    filters,
    page,
    pageSize: PAGE_SIZE,
    assigneeId: currentUserId,
    enabled,
  })

  const pageCount = enabled ? Math.max(1, Math.ceil(total / PAGE_SIZE)) : 1

  return (
    <SectionCard
      title="Mes tickets actifs"
      description="Tickets qui vous sont affectés, ouverts, en cours ou résolus."
      bodyClassName="p-0"
    >
      <TicketsTable
        tickets={enabled ? tickets : []}
        isLoading={enabled && isLoading}
        showAssignee={false}
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

export { MyActiveTicketsTable }
