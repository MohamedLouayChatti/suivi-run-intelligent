import type { components } from "@/types/api";

import type { PermissionGraph } from "./permission-graph";

type PermissionResponse = components["schemas"]["PermissionResponse"];

interface PermissionGroup {
  /** Stable key for open/closed state and jump targets — the label itself, since it is unique. */
  id: string;
  label: string;
  permissions: PermissionResponse[];
}

/**
 * Which module a permission belongs to, read off its name's dot-prefix. Comment and attachment
 * join Tickets rather than standing alone: both are Ticket Management sub-resources whose every
 * permission requires `ticket.read` (`app/scripts/seeding/roles_permissions/permissions.py`), so
 * splitting them into their own groups would only recreate the "hunt in another list" problem
 * this grouping exists to remove. User/role/permission fold into one Auth group for the same
 * reason: `role.assign` and every `permission.grant_*`/`revoke_*` reaches into the other two.
 */
const GROUP_LABEL_BY_PREFIX: Record<string, string> = {
  user: "Utilisateurs, rôles et permissions",
  role: "Utilisateurs, rôles et permissions",
  permission: "Utilisateurs, rôles et permissions",
  ticket: "Tickets",
  comment: "Tickets",
  attachment: "Tickets",
  knowledge_base: "Base de connaissances",
  analytics: "Analytique",
  audit: "Audit",
  notification: "Notifications",
};

const GROUP_ORDER = [
  "Utilisateurs, rôles et permissions",
  "Tickets",
  "Base de connaissances",
  "Analytique",
  "Audit",
  "Notifications",
];

function moduleLabelOf(permissionName: string): string {
  const prefix = permissionName.split(".")[0] ?? permissionName;
  return GROUP_LABEL_BY_PREFIX[prefix] ?? prefix;
}

/**
 * Buckets the flat permission catalog into the module groups above, each ordered so a
 * permission never precedes something it (transitively) requires. `graph.prerequisitesFirst`
 * mirrors the order grants must be sent in, which also happens to be the order that reads best:
 * a prerequisite is always visible before whatever depends on it.
 */
function groupPermissions(
  permissions: readonly PermissionResponse[],
  graph: PermissionGraph
): PermissionGroup[] {
  const byId = new Map(permissions.map((permission) => [permission.id, permission]));
  const idsByLabel = new Map<string, string[]>();
  for (const permission of permissions) {
    const label = moduleLabelOf(permission.name);
    const ids = idsByLabel.get(label);
    if (ids) ids.push(permission.id);
    else idsByLabel.set(label, [permission.id]);
  }

  const labels = [...idsByLabel.keys()].sort((a, b) => {
    const orderA = GROUP_ORDER.indexOf(a);
    const orderB = GROUP_ORDER.indexOf(b);
    if (orderA === -1 && orderB === -1) return a.localeCompare(b);
    if (orderA === -1) return 1;
    if (orderB === -1) return -1;
    return orderA - orderB;
  });

  return labels.map((label) => ({
    id: label,
    label,
    permissions: graph
      .prerequisitesFirst(idsByLabel.get(label) ?? [])
      .map((id) => byId.get(id))
      .filter((permission): permission is PermissionResponse => permission !== undefined),
  }));
}

export { groupPermissions, moduleLabelOf };
export type { PermissionGroup };
