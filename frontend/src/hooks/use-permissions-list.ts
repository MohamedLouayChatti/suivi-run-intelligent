"use client"

import { useQuery } from "@tanstack/react-query"

import { listPermissions } from "@/services/api/users"

const permissionsListQueryKey = ["permissions", "list"] as const

/**
 * GET /auth/permissions — the whole catalog, including each permission's
 * `required_permission_ids`, which is what lets the UI disable a permission whose
 * prerequisites the target does not hold. Gated by `permission.read` on the backend.
 */
function usePermissionsList(options?: { enabled?: boolean }) {
  const enabled = options?.enabled ?? true
  const query = useQuery({
    queryKey: permissionsListQueryKey,
    queryFn: () => listPermissions(),
    enabled,
  })

  return { permissions: query.data ?? [], isLoading: enabled && query.isPending, isError: query.isError }
}

export { usePermissionsList, permissionsListQueryKey }
