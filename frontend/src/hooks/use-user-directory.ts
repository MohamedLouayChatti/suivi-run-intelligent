"use client"

import { useQuery } from "@tanstack/react-query"

import { listUserDirectory } from "@/services/api/users"

const userDirectoryQueryKey = ["users", "directory"] as const

/**
 * GET /auth/users/directory — id, display name, active flag, team and applications, and
 * nothing else. Gated only by `user.read`, which every seeded role holds, so unlike
 * `useUsersList()` this is safe for any authenticated caller: ticket reassign pickers, the
 * tickets/history assignee filters, and the administration user list when the caller lacks
 * `user.read_all`.
 */
function useUserDirectory(options?: { enabled?: boolean }) {
  const enabled = options?.enabled ?? true
  const query = useQuery({
    queryKey: userDirectoryQueryKey,
    queryFn: () => listUserDirectory(),
    enabled,
  })

  return { users: query.data ?? [], isLoading: enabled && query.isPending, isError: query.isError }
}

export { useUserDirectory, userDirectoryQueryKey }
