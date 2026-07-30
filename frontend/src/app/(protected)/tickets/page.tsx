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
import { mockUsers } from "@/features/tickets/mock-data"

export default function TicketsPage() {
  const { tickets, isLoading, addTicket } = useTicketsList()
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
          assignees={mockUsers}
        />
        <MyActiveTicketsTable tickets={tickets} filters={filters} isLoading={isLoading} />
        <TeamActiveTicketsTable tickets={tickets} filters={filters} isLoading={isLoading} />
      </PageBody>
      <CreateTicketDrawer open={drawerOpen} onOpenChange={setDrawerOpen} onCreated={addTicket} />
    </>
  )
}
