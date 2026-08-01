"use client"

import { useQuery } from "@tanstack/react-query"

import { listPermissions } from "@/services/api/users"

const permissionsListQueryKey = ["permissions", "list"] as const

function usePermissionsList() {
  const query = useQuery({
    queryKey: permissionsListQueryKey,
    queryFn: () => listPermissions(),
  })

  return { permissions: query.data ?? [], isLoading: query.isPending, isError: query.isError }
}

export { usePermissionsList, permissionsListQueryKey }
