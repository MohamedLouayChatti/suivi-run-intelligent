"use client"

import { useEffect, useState } from "react"

import type { components } from "@/types/api"
import { getTicketById } from "@/features/tickets/mock-data"

type TicketDetail = components["schemas"]["TicketDetailResponse"]

// Placeholder data source for the Ticket Details page. Replace with a real TanStack Query
// hook backed by services/api/tickets.ts once the endpoint is wired — consumers only depend
// on { ticket, isLoading, notFound, updateTicket }, so swapping the implementation is a
// one-line change.
//
// Callers must remount this hook per ticket id (e.g. `<TicketDetailView key={id} .../>`) —
// it does not reset its own loading state when `id` changes.
function useTicketDetail(id: string) {
  const [ticket, setTicket] = useState<TicketDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => {
      const found = getTicketById(id)
      if (found) {
        setTicket(found)
      } else {
        setNotFound(true)
      }
      setIsLoading(false)
    }, 400)
    return () => clearTimeout(timer)
  }, [id])

  function updateTicket(patch: Partial<TicketDetail>) {
    setTicket((prev) => (prev ? { ...prev, ...patch } : prev))
  }

  return { ticket, isLoading, notFound, updateTicket }
}

export { useTicketDetail }
