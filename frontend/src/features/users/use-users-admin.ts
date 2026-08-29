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

/**
 * A permission save that stopped part-way, carrying how far it got.
 *
 * Permissions are the one write on this page that is not a single request: the sheet's save
 * becomes N grants then M revocations, sent one at a time because the backend's prerequisite
 * rules make their order part of the request. So it is the one write that can leave the
 * account in a state neither the operator asked for nor the one it started in, and the only
 * one that has to say where it stopped — "3 permissions sur 5 accordées" is the difference
 * between knowing what the account now holds and having to work it out.
 *
 * `cause` is the underlying `ApiError`, kept so the caller can describe *why* it stopped.
 */
class PermissionSaveError extends Error {
  readonly granted: number
  readonly revoked: number
  readonly toGrant: number
  readonly toRevoke: number
  readonly cause: unknown

  constructor(granted: number, revoked: number, toGrant: number, toRevoke: number, cause: unknown) {
    super("Permission save stopped part-way")
    this.name = "PermissionSaveError"
    this.granted = granted
    this.revoked = revoked
    this.toGrant = toGrant
    this.toRevoke = toRevoke
    this.cause = cause
  }
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
  //
  // Called on failure as well as on success, everywhere below. A refused write is not the
  // same as a write that did not happen: the permission loop sends many requests and can be
  // refused on any of them, leaving the earlier ones persisted with the cache still showing
  // the state before the save. Invalidating regardless costs one refetch in the cases where
  // nothing landed, and is the only thing that stops the interface actively displaying a
  // user profile the backend no longer holds.
  function afterMutation(groups: QueryKeyPrefix[] = IDENTITY_WRITE) {
    invalidateGroups(queryClient, groups)
  }

  // Wrapped rather than passed by reference: onSuccess is called with (data, variables,
  // context), which would arrive here as `groups`.
  //
  // onSettled rather than onSuccess, for the same reason the three functions below invalidate
  // in a `finally`: what the cache should reflect after a write is what the backend now holds,
  // and that question does not depend on whether the request succeeded.
  const activate = useMutation({ mutationFn: activateUser, onSettled: () => afterMutation() })
  const deactivate = useMutation({ mutationFn: deactivateUser, onSettled: () => afterMutation() })

  // Rejects on refusal, where this used to be fire-and-forget. Both callers handle that: the
  // sheet folds it into the report it shows for the whole save, and the table's row action
  // catches it into a toast. Neither could say anything at all while the rejection was
  // discarded — a self-deactivation 403 simply vanished.
  async function toggleActive(userId: string, currentlyActive: boolean) {
    if (currentlyActive) await deactivate.mutateAsync(userId)
    else await activate.mutateAsync(userId)
  }

  async function changeRole(userId: string, roleId: string) {
    try {
      await setUserRole(userId, roleId)
    } finally {
      // Also the roles list: a role's membership is counted from the user list, and the
      // role a user holds is what decides the permissions their identity resolves to.
      afterMutation(ROLE_WRITE)
    }
  }

  async function saveOrganizationalIdentity(userId: string, identity: OrganizationalIdentity) {
    try {
      await setUserOrganizationalIdentity(userId, identity)
    } finally {
      // The widest of the three. Application assignments are what scope every ticket
      // collection and every analytics figure the user may be answered with, so this does
      // not merely change who they are — it changes which data they see.
      afterMutation(STAFFING_WRITE)
    }
  }

  async function savePermissions(userId: string, toGrant: string[], toRevoke: string[]) {
    let granted = 0
    let revoked = 0
    try {
      // Sequential, and revocations last: a grant whose prerequisite is granted in the same save
      // is refused if it arrives first, and a revocation cascades away dependents the grants may
      // have just added. Promise.all sent them concurrently, which made the outcome depend on
      // arrival order — now that the backend enforces prerequisites, order is part of the request.
      for (const permissionId of toGrant) {
        await grantPermissionToUser(userId, permissionId)
        granted += 1
      }
      for (const permissionId of toRevoke) {
        await revokePermissionFromUser(userId, permissionId)
        revoked += 1
      }
    } catch (error) {
      throw new PermissionSaveError(granted, revoked, toGrant.length, toRevoke.length, error)
    } finally {
      afterMutation()
    }
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

export { useUsersAdmin, PermissionSaveError }
export type { AdminUser, OrganizationalIdentity, UsersAdminCapabilities }
