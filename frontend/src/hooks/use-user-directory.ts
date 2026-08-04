"use client"

import { useQuery } from "@tanstack/react-query"

import { listUserDirectory } from "@/services/api/users"

const userDirectoryQueryKey = ["users", "directory"] as const

/** GET /auth/users/directory — gated only by the user.read permission, so unlike
 * useUsersList()/GET /auth/users this is safe to call for any authenticated user
 * (ticket reassign pickers, tickets/history assignee filters). */
function useUserDirectory() {
  const query = useQuery({
    queryKey: userDirectoryQueryKey,
    queryFn: () => listUserDirectory(),
  })

  return { users: query.data ?? [], isLoading: query.isPending, isError: query.isError }
}

export { useUserDirectory, userDirectoryQueryKey }
