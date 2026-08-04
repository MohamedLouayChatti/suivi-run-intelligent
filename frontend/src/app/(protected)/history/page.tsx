"use client"

import { useEffect, useRef, useState } from "react"

import { PageBody } from "@/components/app/page"
import { HistoryHeader } from "@/features/history/history-header"
import { HistoryFiltersBar } from "@/features/history/history-filters"
import { HistoryTable } from "@/features/history/history-table"
import { useHistoryList } from "@/features/history/use-history-list"
import { defaultHistoryFilters, createDefaultHistoryFilters, type HistoryFilters } from "@/features/history/filter-history"
import { useUsersList } from "@/hooks/use-users-list"
import { useCurrentUser } from "@/lib/auth"
import { getAccessibleApplications, getPrimaryApplication, isAdmin } from "@/services/api/auth"

export default function HistoryPage() {
  const { tickets, isLoading } = useHistoryList()
  const { data: currentUser } = useCurrentUser()
  const admin = currentUser ? isAdmin(currentUser) : false
  const { users } = useUsersList({ enabled: admin })
  const accessibleApplications = currentUser ? getAccessibleApplications(currentUser) : []
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null

  const [filters, setFilters] = useState<HistoryFilters>(defaultHistoryFilters)

  // Filters default to the user's primary application once GET /auth/me resolves, applied
  // exactly once so it never overrides a filter the user has since changed.
  const appliedDefaultRef = useRef(false)
  useEffect(() => {
    if (!appliedDefaultRef.current && primaryApplication) {
      setFilters(createDefaultHistoryFilters(primaryApplication))
      appliedDefaultRef.current = true
    }
  }, [primaryApplication])

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
          onReset={() => setFilters(primaryApplication ? createDefaultHistoryFilters(primaryApplication) : defaultHistoryFilters)}
          assignees={users}
          accessibleApplications={accessibleApplications}
          showAssigneeFilter={admin}
        />
        <HistoryTable tickets={tickets} filters={filters} isLoading={isLoading} />
      </PageBody>
    </>
  )
}
