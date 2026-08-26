"use client"

import { useEffect, useState } from "react"

import { SectionCard } from "@/components/app/page"
import { Pagination } from "@/components/app/pagination"
import { TicketsTable, type DateColumn } from "@/features/tickets/ticket-table"
import { getCompletedAt, type HistoryFilters } from "@/features/history/filter-history"
import { useHistoryList } from "@/features/history/use-history-list"

const PAGE_SIZE = 10

const completedAtColumn: DateColumn[] = [{ label: "Complété le", getValue: getCompletedAt }]

interface HistoryTableProps {
  filters: HistoryFilters
}

function HistoryTable({ filters }: HistoryTableProps) {
  const [page, setPage] = useState(1)

  useEffect(() => setPage(1), [filters])

  const { tickets, total, isLoading } = useHistoryList({ filters, page, pageSize: PAGE_SIZE })
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <SectionCard
      title="Tickets complétés"
      description="Incidents clôturés ou transférés, triés par date de complétion."
      bodyClassName="p-0"
    >
      <TicketsTable
        tickets={tickets}
        isLoading={isLoading}
        showAssignee
        showPriority={false}
        dateColumns={completedAtColumn}
        emptyMessage="Aucun ticket complété ne correspond à vos filtres."
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

export { HistoryTable }
