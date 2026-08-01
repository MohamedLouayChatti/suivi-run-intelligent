import type { components } from "@/types/api"

import { httpClient } from "./client"

type UserResponse = components["schemas"]["UserResponse"]
type RoleResponse = components["schemas"]["RoleResponse"]
type PermissionResponse = components["schemas"]["PermissionResponse"]
type Application = components["schemas"]["Application"]

async function listUsers(pageSize = 100): Promise<UserResponse[]> {
  const { data } = await httpClient.get<UserResponse[]>("/auth/users", {
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

async function assignRole(userId: string, roleId: string): Promise<UserResponse> {
  const { data } = await httpClient.post<UserResponse>(`/auth/users/${userId}/roles/${roleId}`)
  return data
}

async function revokeRole(userId: string, roleId: string): Promise<UserResponse> {
  const { data } = await httpClient.delete<UserResponse>(`/auth/users/${userId}/roles/${roleId}`)
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

function getPrimaryApplication(user: UserResponse): Application | null {
  return user.application_assignments.find((a) => a.assignment_type === "PRIMARY")?.application ?? null
}

function getBackupApplication(user: UserResponse): Application | null {
  return user.application_assignments.find((a) => a.assignment_type === "BACKUP")?.application ?? null
}

export {
  listUsers,
  activateUser,
  deactivateUser,
  assignRole,
  revokeRole,
  listRoles,
  listPermissions,
  getPrimaryApplication,
  getBackupApplication,
}
