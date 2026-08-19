"use client"

import { useQuery } from "@tanstack/react-query"

import { listSimilarIncidents } from "@/services/api/knowledge-base"

function similarIncidentsQueryKey(ticketId: string) {
  return ["knowledge-base", "similar-incidents", ticketId] as const
}

/**
 * GET /knowledge-base/tickets/{id}/similar — gated by `ticket.read` plus the same instance
 * policy as the ticket itself, so anyone who can open this page can read this. Failures are
 * deliberately surfaced rather than swallowed: an empty list and an unreachable knowledge base
 * mean opposite things to the engineer reading the card.
 */
function useSimilarIncidents(ticketId: string) {
  const query = useQuery({
    queryKey: similarIncidentsQueryKey(ticketId),
    queryFn: () => listSimilarIncidents(ticketId),
  })

  return {
    incidents: query.data ?? [],
    isLoading: query.isPending,
    isError: query.isError,
  }
}

export { useSimilarIncidents, similarIncidentsQueryKey }
