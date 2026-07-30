"use client"

import { useState } from "react"

import { PageBody } from "@/components/app/page"
import { HistoryHeader } from "@/features/history/history-header"
import { HistoryFiltersBar } from "@/features/history/history-filters"
import { HistoryTable } from "@/features/history/history-table"
import { useHistoryList } from "@/features/history/use-history-list"
import { defaultHistoryFilters, type HistoryFilters } from "@/features/history/filter-history"
import { mockUsers } from "@/features/tickets/mock-data"

export default function HistoryPage() {
  const { tickets, isLoading } = useHistoryList()
  const [filters, setFilters] = useState<HistoryFilters>(defaultHistoryFilters)

  function handleFilterChange(patch: Partial<HistoryFilters>) {
    setFilters((prev) => ({ ...prev, ...patch }))
  }

  return (
    <>
      <HistoryHeader />
      <PageBody className="space-y-6">
        <HistoryFiltersBar
          filters={filters}
          onChange={handleFilterChange}
          onReset={() => setFilters(defaultHistoryFilters)}
          assignees={mockUsers}
        />
        <HistoryTable tickets={tickets} filters={filters} isLoading={isLoading} />
      </PageBody>
    </>
  )
}
