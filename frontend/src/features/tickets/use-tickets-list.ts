"use client"

import { useEffect, useState } from "react"

import type { components } from "@/types/api"
import { mockTickets } from "@/features/tickets/mock-data"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

// Placeholder data source for the Tickets page. Replace with a real TanStack Query hook
// backed by services/api/tickets.ts once the endpoint is wired — consumers only depend on
// { tickets, isLoading, isError, addTicket }, so swapping the implementation is a one-line change.
function useTicketsList() {
  const [tickets, setTickets] = useState<TicketDetail[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setTickets(mockTickets)
      setIsLoading(false)
    }, 400)
    return () => clearTimeout(timer)
  }, [])

  function addTicket(ticket: TicketDetail) {
    setTickets((prev) => [ticket, ...prev])
  }

  return { tickets, isLoading, isError: false, addTicket }
}

export { useTicketsList }
