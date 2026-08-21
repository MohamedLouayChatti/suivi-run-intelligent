"use client"

import { useState } from "react"

import { useTimedProgressSteps, type TimedProgressStep } from "@/hooks/use-timed-progress-steps"
import type { components } from "@/types/api"

type TicketDetail = components["schemas"]["TicketDetailResponse"]
type TicketCreateRequest = components["schemas"]["TicketCreateRequest"]

/**
 * What creating a ticket actually spends its time on, in the order the backend does it.
 *
 * `POST /tickets` commits the ticket and then, before it answers, embeds the description and
 * searches the corpus for similar incidents — two calls to remote services, which is where
 * essentially all of the ~8 seconds goes. The boundaries below are set from that measurement:
 * the commit is certainly done by one second, and by four and a half we are certainly waiting
 * on the search rather than on the model.
 *
 * These numbers are the whole tuning surface. If the wait moves — a closer model host, a slower
 * one — change them here and nothing else.
 */
const creationSteps: TimedProgressStep[] = [
  { after: 0, label: "Enregistrement du ticket…" },
  { after: 1000, label: "Analyse de la description…" },
  { after: 4500, label: "Recherche d'incidents similaires…" },
]

/** Well past the observed wait: by here, something is genuinely slower than usual. */
const SLOW_AFTER_MS = 20_000

/**
 * Idle, or one of the two phases a submission really has. `uploading` is not on a timer: each
 * attachment is its own request, so which one is in flight is a fact rather than an estimate.
 */
type SubmissionPhase =
  | { kind: "idle" }
  | { kind: "creating" }
  | { kind: "uploading"; index: number; total: number }

interface UseCreateTicketSubmissionOptions {
  onCreated: (payload: TicketCreateRequest) => Promise<TicketDetail>
  onUploadAttachment: (ticketId: string, file: File) => Promise<TicketDetail>
}

/**
 * Owns everything about a create-ticket submission that is not the form's own values: whether one
 * is in flight, what to tell the user while it is, and what went wrong if it did.
 *
 * It is its own hook mainly so the drawer stays a composition of fields. `isSubmitting` is also
 * what stops the second ticket: the button reads it, and before it existed a slow save looked like
 * nothing had happened and got clicked again.
 */
function useCreateTicketSubmission({ onCreated, onUploadAttachment }: UseCreateTicketSubmissionOptions) {
  const [phase, setPhase] = useState<SubmissionPhase>({ kind: "idle" })
  const [error, setError] = useState<string | null>(null)
  const isSubmitting = phase.kind !== "idle"

  // Active for the whole submission rather than the creating phase alone, so the "taking longer
  // than usual" admission covers a slow attachment upload too.
  const { label: timedLabel, isSlow } = useTimedProgressSteps({
    steps: creationSteps,
    isActive: isSubmitting,
    slowAfterMs: SLOW_AFTER_MS,
  })

  const progressLabel =
    phase.kind === "uploading"
      ? `Envoi des pièces jointes (${phase.index}/${phase.total})…`
      : phase.kind === "creating"
        ? timedLabel
        : null

  async function submit(payload: TicketCreateRequest, files: File[]): Promise<boolean> {
    setError(null)
    setPhase({ kind: "creating" })
    try {
      const created = await onCreated(payload)
      for (const [index, file] of files.entries()) {
        setPhase({ kind: "uploading", index: index + 1, total: files.length })
        await onUploadAttachment(created.id, file)
      }
      return true
    } catch (err) {
      // The ticket may already have been created (or partially attached) by the time this
      // throws — report the error rather than losing it, and let the caller keep the drawer open.
      setError(err instanceof Error ? err.message : "Une erreur est survenue.")
      return false
    } finally {
      setPhase({ kind: "idle" })
    }
  }

  return { isSubmitting, progressLabel, isSlow, error, setError, submit }
}

export { useCreateTicketSubmission }
