import type { components } from "@/types/api"

type UserResponse = components["schemas"]["UserResponse"]
type RoleResponse = components["schemas"]["RoleResponse"]

function getRoleName(user: UserResponse, roles: RoleResponse[]): string {
  return roles.find((r) => user.role_ids.includes(r.id))?.name ?? "—"
}

export { getRoleName }
