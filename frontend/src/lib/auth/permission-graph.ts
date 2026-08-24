import type { components } from "@/types/api";

type PermissionResponse = components["schemas"]["PermissionResponse"];

/**
 * The "a capability presupposes its reach" relation, read from the API rather than restated
 * here. `PermissionResponse.required_permission_ids` carries each permission's direct
 * prerequisites, so the UI never carries its own copy of which permission needs which — the
 * same reason `RoleResponse.requires_primary_application` is published.
 *
 * Mirrors the backend's `PermissionDependencyGraph`. Permission-aware UX only: every rule here
 * is enforced again on the server, which refuses an incoherent grant and cascades a revoke
 * whatever the UI shows.
 */
interface PermissionGraph {
  /** Everything `permissionId` transitively needs, itself excluded. */
  prerequisitesOf: (permissionId: string) => Set<string>;
  /** What `held` still lacks before `permissionId` could be used. */
  missingPrerequisites: (permissionId: string, held: ReadonlySet<string>) => Set<string>;
  /** Which of `within` would be cascaded away if `permissionId` were revoked, itself included. */
  cascadeOf: (permissionId: string, within: ReadonlySet<string>) => Set<string>;
  /** The largest subset of `granted` closed under the relation — mirrors `satisfied_subset`. */
  satisfiedSubset: (granted: ReadonlySet<string>) => Set<string>;
  /**
   * `permissionIds` ordered so a permission never precedes something it requires. Grants are
   * one request each and the backend refuses one whose prerequisites are not yet held, so
   * ticking `user.read_all` and `user.activate` together only succeeds if they are sent in
   * that order — which is not the order they arrive in, the catalog being sorted by name.
   */
  prerequisitesFirst: (permissionIds: readonly string[]) => string[];
}

function buildPermissionGraph(permissions: readonly PermissionResponse[]): PermissionGraph {
  const direct = new Map<string, readonly string[]>(
    permissions.map((permission) => [permission.id, permission.required_permission_ids])
  );

  const reverse = new Map<string, string[]>();
  for (const permission of permissions) {
    for (const prerequisite of permission.required_permission_ids) {
      const dependents = reverse.get(prerequisite);
      if (dependents) dependents.push(permission.id);
      else reverse.set(prerequisite, [permission.id]);
    }
  }

  /** Transitive reach from `start`, excluding it. Visited-guarded, so a cycle terminates. */
  function walk(start: string, edges: Map<string, readonly string[]>): Set<string> {
    const reached = new Set<string>();
    const stack = [start];
    while (stack.length > 0) {
      const current = stack.pop() as string;
      for (const neighbour of edges.get(current) ?? []) {
        if (neighbour === start || reached.has(neighbour)) continue;
        reached.add(neighbour);
        stack.push(neighbour);
      }
    }
    return reached;
  }

  function prerequisitesOf(permissionId: string): Set<string> {
    return walk(permissionId, direct);
  }

  return {
    prerequisitesOf,
    missingPrerequisites(permissionId, held) {
      const missing = new Set<string>();
      for (const prerequisite of prerequisitesOf(permissionId)) {
        if (!held.has(prerequisite)) missing.add(prerequisite);
      }
      return missing;
    },
    cascadeOf(permissionId, within) {
      const cascade = new Set<string>([permissionId]);
      for (const dependent of walk(permissionId, reverse)) {
        if (within.has(dependent)) cascade.add(dependent);
      }
      return cascade;
    },
    prerequisitesFirst(permissionIds) {
      const pending = new Set(permissionIds);
      // Depth in the dependency graph orders this correctly and cannot loop: a permission's
      // prerequisites are always strictly shallower than it, so sorting by prerequisite count
      // puts every one of them ahead of it.
      return [...pending].sort((left, right) => {
        const depth = (id: string) => prerequisitesOf(id).size;
        return depth(left) - depth(right);
      });
    },
    satisfiedSubset(granted) {
      let remaining = new Set(granted);
      for (;;) {
        const unsatisfied = new Set<string>();
        for (const permissionId of remaining) {
          const required = direct.get(permissionId) ?? [];
          if (required.some((prerequisite) => !remaining.has(prerequisite))) {
            unsatisfied.add(permissionId);
          }
        }
        if (unsatisfied.size === 0) return remaining;
        remaining = new Set([...remaining].filter((permissionId) => !unsatisfied.has(permissionId)));
      }
    },
  };
}

export { buildPermissionGraph };
export type { PermissionGraph };
