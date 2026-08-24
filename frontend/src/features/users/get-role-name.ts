import type { components } from "@/types/api"

type RoleResponse = components["schemas"]["RoleResponse"]

/** A role's display name, from an id that may be absent — the administration list renders rows
 * from the directory projection too, which carries no role id at all. */
function getRoleName(roleId: string | null | undefined, roles: RoleResponse[]): string {
  return roles.find((role) => role.id === roleId)?.name ?? "—"
}

export { getRoleName }
