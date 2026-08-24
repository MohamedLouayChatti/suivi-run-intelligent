"use client"

import { useQuery } from "@tanstack/react-query"

import { listUsers } from "@/services/api/users"

const usersListQueryKey = ["users", "list"] as const

/**
 * GET /auth/users — the full user records (email, role, staffing, permission exceptions),
 * gated by the `user.read_all` breadth permission. Callers without it must pass
 * `enabled: false` and fall back to `useUserDirectory()`, whose projection needs only
 * `user.read`.
 */
function useUsersList(options?: { enabled?: boolean }) {
  const enabled = options?.enabled ?? true
  const query = useQuery({
    queryKey: usersListQueryKey,
    queryFn: () => listUsers(),
    enabled,
  })

  return { users: query.data ?? [], isLoading: enabled && query.isPending, isError: query.isError }
}

export { useUsersList, usersListQueryKey }
