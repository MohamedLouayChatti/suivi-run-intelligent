"use client"

import { useEffect, useRef, useState } from "react"

import { PageBody } from "@/components/app/page"
import { TicketsHeader } from "@/features/tickets/tickets-header"
import { TicketsFilters } from "@/features/tickets/tickets-filters"
import { MyActiveTicketsTable } from "@/features/tickets/my-active-tickets-table"
import { TeamActiveTicketsTable } from "@/features/tickets/team-active-tickets-table"
import { CreateTicketDrawer } from "@/features/tickets/create-ticket/create-ticket-drawer"
import { useTicketsList } from "@/features/tickets/use-tickets-list"
import { defaultTicketFilters, createDefaultTicketFilters, type TicketFilters } from "@/features/tickets/filter-tickets"
import { useUsersList } from "@/hooks/use-users-list"
import { RequirePermission, useCurrentUser, usePermissions } from "@/lib/auth"
import { getAccessibleApplications, getPrimaryApplication, isAdmin } from "@/services/api/auth"

export default function TicketsPage() {
  const { tickets, isLoading, addTicket } = useTicketsList()
  const { data: currentUser } = useCurrentUser()
  const { hasPermission } = usePermissions()
  const admin = currentUser ? isAdmin(currentUser) : false
  const canCreate = hasPermission("ticket.create")
  const { users } = useUsersList({ enabled: admin })
  const accessibleApplications = currentUser ? getAccessibleApplications(currentUser) : []
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null

  const [filters, setFilters] = useState<TicketFilters>(defaultTicketFilters)
  const [drawerOpen, setDrawerOpen] = useState(false)

  // Filters default to the user's primary application once GET /auth/me resolves, applied
  // exactly once so it never overrides a filter the user has since changed.
  const appliedDefaultRef = useRef(false)
  useEffect(() => {
    if (!appliedDefaultRef.current && primaryApplication) {
      setFilters(createDefaultTicketFilters(primaryApplication))
      appliedDefaultRef.current = true
    }
  }, [primaryApplication])

  function handleFilterChange(patch: Partial<TicketFilters>) {
    setFilters((prev) => ({ ...prev, ...patch }))
  }

  return (
    <RequirePermission permission="ticket.read">
      <TicketsHeader canCreate={canCreate} onCreateClick={() => setDrawerOpen(true)} />
      <PageBody className="space-y-6">
        <TicketsFilters
          filters={filters}
          onChange={handleFilterChange}
          onReset={() => setFilters(primaryApplication ? createDefaultTicketFilters(primaryApplication) : defaultTicketFilters)}
          assignees={users}
          accessibleApplications={accessibleApplications}
          showAssigneeFilter={admin}
        />
        <MyActiveTicketsTable
          tickets={tickets}
          filters={filters}
          isLoading={isLoading}
          currentUserId={currentUser?.id ?? ""}
        />
        <TeamActiveTicketsTable
          tickets={tickets}
          filters={filters}
          isLoading={isLoading}
          currentUserId={currentUser?.id ?? ""}
        />
      </PageBody>
      {canCreate && (
        <CreateTicketDrawer open={drawerOpen} onOpenChange={setDrawerOpen} onCreated={addTicket} />
      )}
    </RequirePermission>
  )
}
