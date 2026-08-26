"use client"

import { useEffect, useRef, useState } from "react"

import { PageBody } from "@/components/app/page"
import { HistoryHeader } from "@/features/history/history-header"
import { HistoryFiltersBar } from "@/features/history/history-filters"
import { HistoryTable } from "@/features/history/history-table"
import { defaultHistoryFilters, createDefaultHistoryFilters, type HistoryFilters } from "@/features/history/filter-history"
import { useUserDirectory } from "@/hooks/use-user-directory"
import { RequireRouteAccess, useCurrentUser, usePermissions } from "@/lib/auth"
import { getAccessibleApplications, getPrimaryApplication } from "@/services/api/auth"
import { exportTicketHistory } from "@/services/api/tickets"

export default function HistoryPage() {
  const { data: currentUser } = useCurrentUser()
  const { hasPermission } = usePermissions()
  // Mirrors the backend's ticket application scope: holding the breadth permission is what lets
  // a caller span every application, rather than belonging to any particular role.
  const canReadAllApplications = hasPermission("ticket.read_any_application")
  const { users } = useUserDirectory()
  const accessibleApplications = currentUser ? getAccessibleApplications(currentUser) : []
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null

  const [filters, setFilters] = useState<HistoryFilters>(defaultHistoryFilters)
  const [isExporting, setIsExporting] = useState(false)

  async function handleExport() {
    setIsExporting(true)
    try {
      const blob = await exportTicketHistory(filters)
      const url = URL.createObjectURL(blob)
      const link = document.createElement("a")
      link.href = url
      link.download = "historique_tickets.csv"
      link.click()
      URL.revokeObjectURL(url)
    } finally {
      setIsExporting(false)
    }
  }

  // Filters default to the user's primary application once GET /auth/me resolves, applied
  // exactly once so it never overrides a filter the user has since changed. A caller who may
  // read every application keeps the cross-application default instead — same rule as the
  // Analyses page, and the view the breadth permission exists to give.
  const appliedDefaultRef = useRef(false)
  useEffect(() => {
    if (appliedDefaultRef.current || !currentUser) return
    if (!canReadAllApplications && primaryApplication) {
      setFilters(createDefaultHistoryFilters(primaryApplication))
    }
    appliedDefaultRef.current = true
  }, [currentUser, canReadAllApplications, primaryApplication])

  function resetFilters() {
    setFilters(
      !canReadAllApplications && primaryApplication
        ? createDefaultHistoryFilters(primaryApplication)
        : defaultHistoryFilters,
    )
  }

  function handleFilterChange(patch: Partial<HistoryFilters>) {
    setFilters((prev) => ({ ...prev, ...patch }))
  }

  return (
    <RequireRouteAccess href="/history">
      <HistoryHeader onExport={handleExport} isExporting={isExporting} />
      <PageBody className="space-y-6">
        <HistoryFiltersBar
          filters={filters}
          onChange={handleFilterChange}
          onReset={resetFilters}
          assignees={users}
          canReadAllApplications={canReadAllApplications}
          accessibleApplications={accessibleApplications}
        />
        <HistoryTable filters={filters} />
      </PageBody>
    </RequireRouteAccess>
  )
}
