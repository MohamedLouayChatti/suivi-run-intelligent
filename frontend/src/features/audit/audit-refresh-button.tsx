"use client"

import { RefreshCw } from "lucide-react"
import { useIsFetching, useQueryClient } from "@tanstack/react-query"

import { Button } from "@/components/ui/button"

import { auditListQueryKey } from "./query-keys"

function AuditRefreshButton() {
  const queryClient = useQueryClient()
  const isFetching = useIsFetching({ queryKey: auditListQueryKey }) > 0

  async function handleRefresh() {
    await queryClient.invalidateQueries({ queryKey: auditListQueryKey })
  }

  return (
    <Button variant="outline" size="sm" onClick={() => void handleRefresh()} disabled={isFetching}>
      <RefreshCw className={isFetching ? "size-4 animate-spin" : "size-4"} />
      Actualiser
    </Button>
  )
}

export { AuditRefreshButton }
