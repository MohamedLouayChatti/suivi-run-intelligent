"use client"

import { useQuery } from "@tanstack/react-query"

import { listRoles } from "@/services/api/users"

const rolesListQueryKey = ["roles", "list"] as const

/** Shared GET /auth/roles list — used by the admin Users role picker and the Roles page. */
function useRolesList() {
  const query = useQuery({
    queryKey: rolesListQueryKey,
    queryFn: () => listRoles(),
  })

  return { roles: query.data ?? [], isLoading: query.isPending, isError: query.isError }
}

export { useRolesList, rolesListQueryKey }
