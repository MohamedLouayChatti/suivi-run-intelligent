"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { grantPermissionToRole, revokePermissionFromRole } from "@/services/api/users"
import { rolesListQueryKey } from "@/hooks/use-roles-list"

function useRolesAdmin() {
  const queryClient = useQueryClient()

  function afterMutation() {
    queryClient.invalidateQueries({ queryKey: rolesListQueryKey })
  }

  const grant = useMutation({
    mutationFn: ({ roleId, permissionId }: { roleId: string; permissionId: string }) =>
      grantPermissionToRole(roleId, permissionId),
    onSuccess: afterMutation,
  })
  const revoke = useMutation({
    mutationFn: ({ roleId, permissionId }: { roleId: string; permissionId: string }) =>
      revokePermissionFromRole(roleId, permissionId),
    onSuccess: afterMutation,
  })

  function togglePermission(roleId: string, permissionId: string, desiredGranted: boolean) {
    if (desiredGranted) grant.mutate({ roleId, permissionId })
    else revoke.mutate({ roleId, permissionId })
  }

  return { togglePermission }
}

export { useRolesAdmin }
