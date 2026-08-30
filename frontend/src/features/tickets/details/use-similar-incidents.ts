"use client"

import { useEffect, useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { listSimilarIncidents } from "@/services/api/knowledge-base"

/**
 * How often to re-ask while the backend reports the analysis as still running, and how long to
 * keep asking before giving up on it.
 *
 * The analysis is a background job whose slow step is an embedding call, which on a cold model can
 * take a good few seconds; five is short enough that the card fills in while the reader is still
 * looking at it, and long enough not to hammer the endpoint. The ceiling exists because PENDING has
 * no failure state to distinguish it from: a job that raised, and a ticket created before this
 * module ever ran, both stay PENDING forever. Polling until the end of time would spin an "en
 * cours" message at a reader for whom nothing is in fact in progress.
 */
const PENDING_POLL_INTERVAL_MS = 5_000
const PENDING_POLL_TIMEOUT_MS = 120_000

function similarIncidentsQueryKey(ticketId: string) {
  return ["knowledge-base", "similar-incidents", ticketId] as const
}

/**
 * GET /knowledge-base/tickets/{id}/similar — gated by `ticket.read` plus the same instance
 * policy as the ticket itself, so anyone who can open this page can read this. Failures are
 * deliberately surfaced rather than swallowed: an empty list and an unreachable knowledge base
 * mean opposite things to the engineer reading the card.
 *
 * "Not analysed yet" is a third such meaning, and the reason this polls at all. A newly created
 * ticket is analysed in a background job rather than in the request that created it, so a reader
 * who opens it immediately arrives before there is anything to show. The query re-runs on an
 * interval for as long as the backend says PENDING, and stops the moment it says READY — the
 * common case, an older ticket, is answered READY on the first fetch and never polls.
 *
 * `hasTimedOut` is reported separately rather than folded into `isAnalysisPending` because the two
 * ask for different copy: one says the analysis is running, the other that it is not going to
 * finish and the card should stop claiming otherwise.
 */
function useSimilarIncidents(ticketId: string) {
  // The deadline as state flipped by a timer, rather than an elapsed time computed while
  // rendering. Reading the clock during render is impure and the lint rules reject it, as they do a
  // ref read during render and a synchronous setState inside an effect — a timer callback is the
  // one place a value like this may be produced. It also renders on its own when it fires, which is
  // what lets the card stop claiming the analysis is running without waiting for another response.
  //
  // Started at mount rather than at the first PENDING answer: they are one request's latency apart,
  // and the detail view is mounted with `key={id}`, so moving to another ticket remounts this hook
  // and starts the clock over on its own.
  const [hasWaitedLongEnough, setHasWaitedLongEnough] = useState(false)

  useEffect(() => {
    const timer = setTimeout(() => setHasWaitedLongEnough(true), PENDING_POLL_TIMEOUT_MS)
    return () => clearTimeout(timer)
  }, [])

  const query = useQuery({
    queryKey: similarIncidentsQueryKey(ticketId),
    queryFn: () => listSimilarIncidents(ticketId),
    refetchInterval: (q) =>
      q.state.data?.status === "PENDING" && !hasWaitedLongEnough ? PENDING_POLL_INTERVAL_MS : false,
  })

  const isAnalysisPending = query.data?.status === "PENDING"

  return {
    incidents: query.data?.incidents ?? [],
    isLoading: query.isPending,
    isError: query.isError,
    isAnalysisPending: isAnalysisPending && !hasWaitedLongEnough,
    hasTimedOut: isAnalysisPending && hasWaitedLongEnough,
  }
}

export { useSimilarIncidents, similarIncidentsQueryKey }
