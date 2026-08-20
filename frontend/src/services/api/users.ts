import type { components } from "@/types/api"

import { httpClient } from "./client"

type UserResponse = components["schemas"]["UserResponse"]
type UserDirectoryResponse = components["schemas"]["UserDirectoryResponse"]
type RoleResponse = components["schemas"]["RoleResponse"]
type PermissionResponse = components["schemas"]["PermissionResponse"]
type Application = components["schemas"]["Application"]

async function listUsers(pageSize = 100): Promise<UserResponse[]> {
  const { data } = await httpClient.get<UserResponse[]>("/auth/users", {
    params: { page: 1, page_size: pageSize },
  })
  return data
}

/** GET /auth/users/directory — user.read only, no admin gate. Returns id/display_name/
 * active/functional_team/application_assignments, used to populate reassign pickers and
 * assignee filters for any user, unlike the admin-only listUsers() above. */
async function listUserDirectory(pageSize = 100): Promise<UserDirectoryResponse[]> {
  const { data } = await httpClient.get<UserDirectoryResponse[]>("/auth/users/directory", {
    params: { page: 1, page_size: pageSize },
  })
  return data
}

async function activateUser(userId: string): Promise<UserResponse> {
  const { data } = await httpClient.post<UserResponse>(`/auth/users/${userId}/activate`)
  return data
}

async function deactivateUser(userId: string): Promise<UserResponse> {
  const { data } = await httpClient.post<UserResponse>(`/auth/users/${userId}/deactivate`)
  return data
}

/** PUT /auth/users/:id/role/:roleId — sets the user's one role, replacing whatever they held.
 * A single call rather than the revoke-then-assign pair this used to need: a user holds
 * exactly one role, so changing it is one request. */
async function setUserRole(userId: string, roleId: string): Promise<UserResponse> {
  const { data } = await httpClient.put<UserResponse>(`/auth/users/${userId}/role/${roleId}`)
  return data
}

async function listRoles(pageSize = 100): Promise<RoleResponse[]> {
  const { data } = await httpClient.get<RoleResponse[]>("/auth/roles", {
    params: { page: 1, page_size: pageSize },
  })
  return data
}

async function listPermissions(pageSize = 100): Promise<PermissionResponse[]> {
  const { data } = await httpClient.get<PermissionResponse[]>("/auth/permissions", {
    params: { page: 1, page_size: pageSize },
  })
  return data
}

async function grantPermissionToUser(userId: string, permissionId: string): Promise<UserResponse> {
  const { data } = await httpClient.post<UserResponse>(`/auth/users/${userId}/permissions/${permissionId}`)
  return data
}

async function revokePermissionFromUser(userId: string, permissionId: string): Promise<UserResponse> {
  const { data } = await httpClient.delete<UserResponse>(`/auth/users/${userId}/permissions/${permissionId}`)
  return data
}

async function grantPermissionToRole(roleId: string, permissionId: string): Promise<RoleResponse> {
  const { data } = await httpClient.post<RoleResponse>(`/auth/roles/${roleId}/permissions/${permissionId}`)
  return data
}

async function revokePermissionFromRole(roleId: string, permissionId: string): Promise<RoleResponse> {
  const { data } = await httpClient.delete<RoleResponse>(`/auth/roles/${roleId}/permissions/${permissionId}`)
  return data
}

function getPrimaryApplication(user: UserResponse): Application | null {
  return user.application_assignments.find((a) => a.assignment_type === "PRIMARY")?.application ?? null
}

function getBackupApplication(user: UserResponse): Application | null {
  return user.application_assignments.find((a) => a.assignment_type === "BACKUP")?.application ?? null
}

export {
  listUsers,
  listUserDirectory,
  activateUser,
  deactivateUser,
  setUserRole,
  listRoles,
  listPermissions,
  grantPermissionToUser,
  revokePermissionFromUser,
  grantPermissionToRole,
  revokePermissionFromRole,
  getPrimaryApplication,
  getBackupApplication,
}
