"use client"

import { useQuery } from "@tanstack/react-query"

import { listUsers } from "@/services/api/users"

const usersListQueryKey = ["users", "list"] as const

/** Shared GET /auth/users list — used wherever a page needs the full user directory
 * (ticket assignee pickers/filters, admin user management). TanStack Query dedupes
 * concurrent callers under this same query key. GET /auth/users is admin-only on the
 * backend (403 otherwise) — pass `enabled: false` for non-admin callers so it's never fired. */
function useUsersList(options?: { enabled?: boolean }) {
  const query = useQuery({
    queryKey: usersListQueryKey,
    queryFn: () => listUsers(),
    enabled: options?.enabled ?? true,
  })

  return { users: query.data ?? [], isLoading: query.isPending, isError: query.isError }
}

export { useUsersList, usersListQueryKey }
