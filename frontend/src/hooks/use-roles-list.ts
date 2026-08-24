"use client"

import { useQuery } from "@tanstack/react-query"

import { listRoles } from "@/services/api/users"

const rolesListQueryKey = ["roles", "list"] as const

/**
 * Shared GET /auth/roles list — used by the admin Users role picker and the Roles page.
 * Gated by `role.read_all` on the backend, so callers holding only `role.read` must pass
 * `enabled: false` rather than fire a request that can only 403.
 */
function useRolesList(options?: { enabled?: boolean }) {
  const enabled = options?.enabled ?? true
  const query = useQuery({
    queryKey: rolesListQueryKey,
    queryFn: () => listRoles(),
    enabled,
  })

  return { roles: query.data ?? [], isLoading: enabled && query.isPending, isError: query.isError }
}

export { useRolesList, rolesListQueryKey }
