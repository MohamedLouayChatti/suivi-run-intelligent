"use client";

import type { ReactNode } from "react";

import { AccessDeniedScreen } from "@/components/app/access-denied";
import { routeRequirements } from "@/components/layout/nav-config";

import { usePermissions } from "./use-permissions";

/**
 * The page half of a route's single declared requirement. `href` keys into `routeRequirements`,
 * the same entry the sidebar filters its link against, so an entry a user can see is an entry
 * that opens — the drift between two separate declarations is what produced an Access-Denied
 * screen behind a visible sidebar icon.
 *
 * Renders the Access-Denied screen rather than redirecting, and always runs inside AuthGate, so
 * the current user is already resolved. A route with no entry is open to any authenticated user,
 * matching the sidebar.
 *
 * Gates are always permission names, never roles — and deliberately the *least* a caller needs
 * for the page to be worth opening. Everything finer is decided by the sections themselves, each
 * asking for the permission its own endpoint requires.
 */
function RequireRouteAccess({ href, children }: { href: string; children: ReactNode }) {
  const { hasPermission, hasAnyPermission } = usePermissions();
  const requirement = routeRequirements[href];

  if (requirement !== undefined) {
    const allowed =
      (requirement.permission === undefined || hasPermission(requirement.permission)) &&
      (requirement.anyPermission === undefined || hasAnyPermission(requirement.anyPermission));
    if (!allowed) return <AccessDeniedScreen />;
  }

  return <>{children}</>;
}

export { RequireRouteAccess };
