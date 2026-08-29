"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  activateUser,
  deactivateUser,
  setUserRole,
  setUserOrganizationalIdentity,
  grantPermissionToUser,
  revokePermissionFromUser,
} from "@/services/api/users"
import { useUsersList } from "@/hooks/use-users-list"
import { useUserDirectory } from "@/hooks/use-user-directory"
import { usePermissions } from "@/lib/auth"
import {
  IDENTITY_WRITE,
  ROLE_WRITE,
  STAFFING_WRITE,
  invalidateGroups,
  type QueryKeyPrefix,
} from "@/lib/cache-invalidation"
import type { components } from "@/types/api"

type OrganizationalIdentity = components["schemas"]["UserOrganizationalIdentityRequest"]
type UserResponse = components["schemas"]["UserResponse"]
type UserDirectoryResponse = components["schemas"]["UserDirectoryResponse"]

/**
 * A row of the administration user list, from whichever projection the caller may read.
 *
 * `detail` carries the fields only `user.read_all` exposes — email, role, permission exceptions
 * — and is `null` for a caller reading the directory instead. Keeping the two in one row rather
 * than branching the whole page is what lets each column and each action ask for the permission
 * it actually needs: someone holding `user.activate` alone still gets a list of names to act
 * on, without being shown an email address they may not read.
 */
interface AdminUser {
  id: string
  display_name: string
  active: boolean
  functional_team: UserDirectoryResponse["functional_team"]
  application_assignments: UserDirectoryResponse["application_assignments"]
  avatar_url: string | null
  detail: UserResponse | null
}

/** What the current user may do on this page — each mirroring one backend permission. */
interface UsersAdminCapabilities {
  readAll: boolean
  activate: boolean
  deactivate: boolean
  assignRole: boolean
  manageOrganization: boolean
  managePermissions: boolean
  readRoles: boolean
  readPermissions: boolean
}

function useUsersAdmin() {
  const { hasPermission } = usePermissions()
  const queryClient = useQueryClient()

  const capabilities: UsersAdminCapabilities = {
    readAll: hasPermission("user.read_all"),
    activate: hasPermission("user.activate"),
    deactivate: hasPermission("user.deactivate"),
    assignRole: hasPermission("role.assign"),
    manageOrganization: hasPermission("user.manage_organization"),
    // Both halves of editing a user's permission exceptions. The sheet writes grants and
    // revocations together in one save, so it renders only for a caller who may do both.
    managePermissions:
      hasPermission("permission.grant_to_user") && hasPermission("permission.revoke_from_user"),
    readRoles: hasPermission("role.read_all"),
    readPermissions: hasPermission("permission.read"),
  }

  // Exactly one of these fires. The directory is the fallback rather than a lesser version of
  // the same request: it is a different endpoint with a different projection, gated by the
  // `user.read` every seeded role holds.
  const full = useUsersList({ enabled: capabilities.readAll })
  const directory = useUserDirectory({ enabled: !capabilities.readAll })

  const users: AdminUser[] = capabilities.readAll
    ? full.users.map((user) => ({
        id: user.id,
        display_name: user.display_name,
        active: user.active,
        functional_team: user.functional_team,
        application_assignments: user.application_assignments,
        avatar_url: user.avatar_url ?? null,
        detail: user,
      }))
    : directory.users.map((user) => ({
        id: user.id,
        display_name: user.display_name,
        active: user.active,
        functional_team: user.functional_team,
        application_assignments: user.application_assignments,
        avatar_url: null,
        detail: null,
      }))

  // Which caches a write here disturbs depends on what it wrote, so each path names its
  // own group. What they share is the identity half, and that is the part that was
  // missing: /auth/me is fetched once per session and backs every permission-gated
  // control in the app, including for the administrator performing the change. Both ways
  // they can reach themselves — granting themselves a permission directly, or granting
  // one to a role they hold — left their own capabilities stale until a hard refresh.
  function afterMutation(groups: QueryKeyPrefix[] = IDENTITY_WRITE) {
    invalidateGroups(queryClient, groups)
  }

  // Wrapped rather than passed by reference: onSuccess is called with (data, variables,
  // context), which would arrive here as `groups`.
  const activate = useMutation({ mutationFn: activateUser, onSuccess: () => afterMutation() })
  const deactivate = useMutation({ mutationFn: deactivateUser, onSuccess: () => afterMutation() })

  function toggleActive(userId: string, currentlyActive: boolean) {
    if (currentlyActive) deactivate.mutate(userId)
    else activate.mutate(userId)
  }

  async function changeRole(userId: string, roleId: string) {
    await setUserRole(userId, roleId)
    // Also the roles list: a role's membership is counted from the user list, and the
    // role a user holds is what decides the permissions their identity resolves to.
    afterMutation(ROLE_WRITE)
  }

  async function saveOrganizationalIdentity(userId: string, identity: OrganizationalIdentity) {
    await setUserOrganizationalIdentity(userId, identity)
    // The widest of the three. Application assignments are what scope every ticket
    // collection and every analytics figure the user may be answered with, so this does
    // not merely change who they are — it changes which data they see.
    afterMutation(STAFFING_WRITE)
  }

  async function savePermissions(userId: string, toGrant: string[], toRevoke: string[]) {
    // Sequential, and revocations last: a grant whose prerequisite is granted in the same save
    // is refused if it arrives first, and a revocation cascades away dependents the grants may
    // have just added. Promise.all sent them concurrently, which made the outcome depend on
    // arrival order — now that the backend enforces prerequisites, order is part of the request.
    for (const permissionId of toGrant) await grantPermissionToUser(userId, permissionId)
    for (const permissionId of toRevoke) await revokePermissionFromUser(userId, permissionId)
    afterMutation()
  }

  return {
    users,
    capabilities,
    isLoading: capabilities.readAll ? full.isLoading : directory.isLoading,
    toggleActive,
    changeRole,
    saveOrganizationalIdentity,
    savePermissions,
  }
}

export { useUsersAdmin }
export type { AdminUser, OrganizationalIdentity, UsersAdminCapabilities }
