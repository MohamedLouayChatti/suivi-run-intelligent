"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  asImportRejection,
  importTicketBatch,
  type BatchImportRejection,
  type BatchImportReport,
} from "@/services/api/knowledge-base"
import { describeKnowledgeBaseError } from "@/features/knowledge-base/error-messages"
import { recalculationScheduleQueryKey } from "@/features/knowledge-base/use-recalculation-schedule"
import { ticketsListQueryKey } from "@/features/tickets/use-tickets-list"
import type { components } from "@/types/api"

type Application = components["schemas"]["Application"]

/** What one attempted import ended as — exactly one of these at a time. */
type BatchImportOutcome =
  | { kind: "success"; report: BatchImportReport; fileName: string }
  | { kind: "rejected"; rejection: BatchImportRejection; fileName: string }
  | { kind: "failed"; message: string }

function useBatchImport() {
  const queryClient = useQueryClient()

  const mutation = useMutation<
    BatchImportOutcome,
    unknown,
    { application: Application; file: File }
  >({
    mutationFn: async ({ application, file }) => {
      try {
        const report = await importTicketBatch(application, file)
        return { kind: "success", report, fileName: file.name }
      } catch (error) {
        // A rejected file is an outcome to render, not an exception to surface: the operator's
        // next action is reading the report, and every other failure is a sentence in a banner.
        const rejection = asImportRejection(error)
        if (rejection) {
          return { kind: "rejected", rejection, fileName: file.name }
        }
        return { kind: "failed", message: describeKnowledgeBaseError(error) }
      }
    },
    onSuccess: (outcome) => {
      if (outcome.kind !== "success") return
      // The tickets are durable by the time this returns, and the import enqueues a full
      // recalculation — so both the ticket list and the schedule's `running` flag are stale.
      queryClient.invalidateQueries({ queryKey: ticketsListQueryKey })
      queryClient.invalidateQueries({ queryKey: recalculationScheduleQueryKey })
    },
  })

  return {
    outcome: mutation.data ?? null,
    isImporting: mutation.isPending,
    runImport: (application: Application, file: File) => mutation.mutate({ application, file }),
    reset: () => mutation.reset(),
  }
}

export { useBatchImport }
export type { BatchImportOutcome }
