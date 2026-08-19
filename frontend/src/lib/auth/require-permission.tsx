"use client";

import type { ReactNode } from "react";

import { AccessDeniedScreen } from "@/components/app/access-denied";

import { usePermissions } from "./use-permissions";

interface RequirePermissionProps {
  /** A single permission name the current user's effective permissions must include. */
  permission?: string;
  /** Several permission names, all of which must be held — mirrors `require_permissions`. */
  permissions?: readonly string[];
  /**
   * Several permission names, at least one of which must be held. For a page that composes
   * capabilities gated separately on the backend (the Knowledge Base admin page: batch import
   * and recalculation management), where holding any one of them is reason to reach the page
   * and each section decides for itself whether to render.
   */
  anyPermissions?: readonly string[];
  children: ReactNode;
}

/**
 * Route-level permission-aware UX: renders an Access-Denied screen instead of the page when the
 * current user is known to lack access, rather than silently redirecting. Always runs inside
 * AuthGate, so the current user is already resolved here.
 *
 * Gates are always permission names — never roles. Pages that used to be "admin only" now name
 * the breadth permission the backend actually checks (`user.read_all`, `role.read_all`,
 * `audit.read`, …), so granting that permission to another role, or directly to one user, opens
 * the page without any frontend change.
 */
function RequirePermission({
  permission,
  permissions,
  anyPermissions,
  children,
}: RequirePermissionProps) {
  const { hasPermission, hasAllPermissions, hasAnyPermission } = usePermissions();

  const allowed =
    (permission === undefined || hasPermission(permission)) &&
    (permissions === undefined || hasAllPermissions(permissions)) &&
    (anyPermissions === undefined || hasAnyPermission(anyPermissions));

  if (!allowed) {
    return <AccessDeniedScreen />;
  }

  return <>{children}</>;
}

export { RequirePermission };
