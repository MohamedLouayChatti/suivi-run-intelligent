"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { toast } from "@/hooks/use-toast"
import {
  getRecalculationSchedule,
  runRecalculationNow,
  updateRecalculationSchedule,
  type UpdateRecalculationSchedule,
} from "@/services/api/knowledge-base"
import { describeKnowledgeBaseError } from "@/features/knowledge-base/error-messages"

const recalculationScheduleQueryKey = ["knowledge-base", "recalculation-schedule"] as const

/**
 * How often the schedule is re-read while the page is open. `running` and `next_run_at` are both
 * read off the live scheduler rather than stored, so they go stale on their own — a pass started
 * from another tab, or one that finished, shows up within this window without the operator
 * reloading. Slow enough not to be a poll of any consequence.
 */
const SCHEDULE_REFETCH_INTERVAL_MS = 20_000

function useRecalculationSchedule({ canManage }: { canManage: boolean }) {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: recalculationScheduleQueryKey,
    queryFn: () => getRecalculationSchedule(),
    refetchInterval: SCHEDULE_REFETCH_INTERVAL_MS,
  })

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: recalculationScheduleQueryKey })
  }

  const save = useMutation({
    mutationFn: (payload: UpdateRecalculationSchedule) => updateRecalculationSchedule(payload),
    onSuccess: (schedule) => {
      queryClient.setQueryData(recalculationScheduleQueryKey, schedule)
      toast({
        title: "Planification enregistrée",
        description: schedule.enabled
          ? "Le recalcul complet suivra désormais cette planification."
          : "Le recalcul complet planifié est désactivé. Vous pouvez toujours lancer une passe manuellement.",
      })
    },
    onError: (error) => {
      toast({
        variant: "destructive",
        title: "Enregistrement impossible",
        description: describeKnowledgeBaseError(error),
      })
    },
  })

  const runNow = useMutation({
    mutationFn: () => runRecalculationNow(),
    onSuccess: () => {
      invalidate()
      toast({
        title: "Recalcul lancé",
        description:
          "La passe s'exécute en arrière-plan et peut durer plusieurs minutes. Son état est indiqué ci-dessus.",
      })
    },
    onError: (error) => {
      invalidate()
      toast({
        variant: "destructive",
        title: "Recalcul non lancé",
        description: describeKnowledgeBaseError(error),
      })
    },
  })

  return {
    schedule: query.data ?? null,
    isLoading: query.isPending,
    isError: query.isError,
    // Read access and management are separate permissions on the backend, so a caller may legitimately
    // be able to see the schedule and not change it.
    canManage,
    isSaving: save.isPending,
    isStarting: runNow.isPending,
    onSave: (payload: UpdateRecalculationSchedule) => save.mutate(payload),
    onRunNow: () => runNow.mutate(),
  }
}

export { useRecalculationSchedule, recalculationScheduleQueryKey }
