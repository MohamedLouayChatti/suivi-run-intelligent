"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { grantPermissionToRole, revokePermissionFromRole } from "@/services/api/users"
import { rolesListQueryKey } from "@/hooks/use-roles-list"
import { usePermissions } from "@/lib/auth"

/** What the current user may do to a role's permission set — one flag per backend permission. */
interface RolesAdminCapabilities {
  grantPermission: boolean
  revokePermission: boolean
  readPermissions: boolean
  countMembers: boolean
}

function useRolesAdmin() {
  const { hasPermission } = usePermissions()
  const queryClient = useQueryClient()

  const capabilities: RolesAdminCapabilities = {
    grantPermission: hasPermission("permission.grant_to_role"),
    revokePermission: hasPermission("permission.revoke_from_role"),
    readPermissions: hasPermission("permission.read"),
    // Member counts are the one thing on this page needing `user.read_all`. A decorative
    // statistic used to drag that breadth permission into the gate for the whole page; now it
    // is simply absent for callers who may not read every user.
    countMembers: hasPermission("user.read_all"),
  }

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

  return { capabilities, togglePermission }
}

export { useRolesAdmin }
export type { RolesAdminCapabilities }
