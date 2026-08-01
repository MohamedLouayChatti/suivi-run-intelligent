"use client"

import { useState } from "react"

import { PageBody } from "@/components/app/page"
import { TicketsHeader } from "@/features/tickets/tickets-header"
import { TicketsFilters } from "@/features/tickets/tickets-filters"
import { MyActiveTicketsTable } from "@/features/tickets/my-active-tickets-table"
import { TeamActiveTicketsTable } from "@/features/tickets/team-active-tickets-table"
import { CreateTicketDrawer } from "@/features/tickets/create-ticket/create-ticket-drawer"
import { useTicketsList } from "@/features/tickets/use-tickets-list"
import { defaultTicketFilters, type TicketFilters } from "@/features/tickets/filter-tickets"
import { useUsersList } from "@/hooks/use-users-list"
import { useCurrentUser } from "@/lib/auth"

export default function TicketsPage() {
  const { tickets, isLoading, addTicket } = useTicketsList()
  const { users } = useUsersList()
  const { data: currentUser } = useCurrentUser()
  const [filters, setFilters] = useState<TicketFilters>(defaultTicketFilters)
  const [drawerOpen, setDrawerOpen] = useState(false)

  function handleFilterChange(patch: Partial<TicketFilters>) {
    setFilters((prev) => ({ ...prev, ...patch }))
  }

  return (
    <>
      <TicketsHeader onCreateClick={() => setDrawerOpen(true)} />
      <PageBody className="space-y-6">
        <TicketsFilters
          filters={filters}
          onChange={handleFilterChange}
          onReset={() => setFilters(defaultTicketFilters)}
          assignees={users}
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
      <CreateTicketDrawer open={drawerOpen} onOpenChange={setDrawerOpen} onCreated={addTicket} />
    </>
  )
}
