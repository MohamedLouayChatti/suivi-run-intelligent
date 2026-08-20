"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  activateUser,
  deactivateUser,
  setUserRole,
  grantPermissionToUser,
  revokePermissionFromUser,
} from "@/services/api/users"
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

  async function changeRole(userId: string, roleId: string) {
    await setUserRole(userId, roleId)
    afterMutation()
  }

  async function savePermissions(userId: string, toGrant: string[], toRevoke: string[]) {
    await Promise.all([
      ...toGrant.map((permissionId) => grantPermissionToUser(userId, permissionId)),
      ...toRevoke.map((permissionId) => revokePermissionFromUser(userId, permissionId)),
    ])
    afterMutation()
  }

  return { users, isLoading, toggleActive, changeRole, savePermissions }
}

export { useUsersAdmin }
