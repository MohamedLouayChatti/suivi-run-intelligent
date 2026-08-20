import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]
type RoleResponse = components["schemas"]["RoleResponse"]

function getRoleName(user: UserResponse, roles: RoleResponse[]): string {
  return roles.find((r) => r.id === user.role_id)?.name ?? "—"
}

export { getRoleName }
