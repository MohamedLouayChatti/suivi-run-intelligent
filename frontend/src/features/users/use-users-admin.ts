"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { activateUser, deactivateUser, assignRole, revokeRole } from "@/services/api/users"
import { useUsersList, usersListQueryKey } from "@/hooks/use-users-list"

function useUsersAdmin() {
  const { users, isLoading } = useUsersList()
  const queryClient = useQueryClient()

  function afterMutation() {
    queryClient.invalidateQueries({ queryKey: usersListQueryKey })
  }

  const activate = useMutation({ mutationFn: activateUser, onSuccess: afterMutation })
  const deactivate = useMutation({ mutationFn: deactivateUser, onSuccess: afterMutation })

  function toggleActive(userId: string, currentlyActive: boolean) {
    if (currentlyActive) deactivate.mutate(userId)
    else activate.mutate(userId)
  }

  // The admin UI presents role assignment as a single-select dropdown, while the backend
  // models roles as many-to-many with separate assign/revoke endpoints — revoke whatever the
  // user currently holds and assign the newly picked one to preserve that single-select UX.
  async function changeRole(userId: string, roleId: string, currentRoleIds: string[]) {
    await Promise.all(currentRoleIds.filter((id) => id !== roleId).map((id) => revokeRole(userId, id)))
    if (!currentRoleIds.includes(roleId)) {
      await assignRole(userId, roleId)
    }
    afterMutation()
  }

  return { users, isLoading, toggleActive, changeRole }
}

export { useUsersAdmin }
