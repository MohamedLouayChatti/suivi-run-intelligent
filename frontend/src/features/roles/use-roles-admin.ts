"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { grantPermissionToRole, revokePermissionFromRole } from "@/services/api/users"
import { usePermissions } from "@/lib/auth"
import { ROLE_WRITE, invalidateGroups } from "@/lib/cache-invalidation"

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

  // The roles list was the only thing refreshed here, which missed the change's real
  // reach: a role is a bundle of permissions held by everyone in it, so editing one
  // rewrites the effective permissions of every member — the administrator making the
  // edit included, whenever they hold the role they are editing.
  function afterMutation() {
    invalidateGroups(queryClient, ROLE_WRITE)
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
