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
import { useUserDirectory } from "@/hooks/use-user-directory"
import { RequireRouteAccess, useCurrentUser, usePermissions } from "@/lib/auth"
import { getAccessibleApplications, getPrimaryApplication } from "@/services/api/auth"

export default function TicketsPage() {
  const { tickets, isLoading, addTicket, uploadAttachment } = useTicketsList()
  const { data: currentUser } = useCurrentUser()
  const { hasPermission } = usePermissions()
  const accessibleApplications = currentUser ? getAccessibleApplications(currentUser) : []
  // Mirrors TicketCreationPolicy, not just the permission: creating a ticket also requires an
  // assignment to the application it is filed against, with no breadth override. Someone holding
  // `ticket.create` but staffed nowhere has no application to file against, and the drawer's
  // application picker would be empty — a form that cannot be submitted.
  const canCreate = hasPermission("ticket.create") && accessibleApplications.length > 0
  // Mirrors the backend's ticket application scope: holding the breadth permission is what lets
  // a caller span every application, rather than belonging to any particular role.
  const canReadAllApplications = hasPermission("ticket.read_any_application")
  const { users } = useUserDirectory()
  const primaryApplication = currentUser ? getPrimaryApplication(currentUser) : null

  const [filters, setFilters] = useState<TicketFilters>(defaultTicketFilters)
  const [drawerOpen, setDrawerOpen] = useState(false)

  // Filters default to the user's primary application once GET /auth/me resolves, applied
  // exactly once so it never overrides a filter the user has since changed. A caller who may
  // read every application keeps the cross-application default instead — same rule as the
  // Analyses page, and the view the breadth permission exists to give.
  const appliedDefaultRef = useRef(false)
  useEffect(() => {
    if (appliedDefaultRef.current || !currentUser) return
    if (!canReadAllApplications && primaryApplication) {
      setFilters(createDefaultTicketFilters(primaryApplication))
    }
    appliedDefaultRef.current = true
  }, [currentUser, canReadAllApplications, primaryApplication])

  function resetFilters() {
    setFilters(
      !canReadAllApplications && primaryApplication
        ? createDefaultTicketFilters(primaryApplication)
        : defaultTicketFilters,
    )
  }

  function handleFilterChange(patch: Partial<TicketFilters>) {
    setFilters((prev) => ({ ...prev, ...patch }))
  }

  return (
    <RequireRouteAccess href="/tickets">
      <TicketsHeader canCreate={canCreate} onCreateClick={() => setDrawerOpen(true)} />
      <PageBody className="space-y-6">
        <TicketsFilters
          filters={filters}
          onChange={handleFilterChange}
          onReset={resetFilters}
          assignees={users}
          canReadAllApplications={canReadAllApplications}
          accessibleApplications={accessibleApplications}
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
        <CreateTicketDrawer
          open={drawerOpen}
          onOpenChange={setDrawerOpen}
          onCreated={addTicket}
          onUploadAttachment={uploadAttachment}
        />
      )}
    </RequireRouteAccess>
  )
}
